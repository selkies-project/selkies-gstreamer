// src/gamepad.rs

use tokio::net::{UnixListener, UnixStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::mpsc::{self, Sender, Receiver};
use tokio::sync::Mutex;
use std::sync::Arc;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use std::path::Path;
use std::fs;
use bytes::{BufMut, BytesMut};
use log::{info, debug, error, warn};
use std::io;
use std::os::unix::io::AsRawFd;
use std::mem;
use input_event_codes::*;

const MAX_BTNS: usize = 512;
const MAX_AXES: usize = 64;
const ABS_MIN: i32 = -32767;
const ABS_MAX: i32 = 32767;

// Utility functions for normalization
fn normalize_axis_val(val: f32) -> i32 {
    let normalized = ABS_MIN as f32 + ((val + 1.0) * ((ABS_MAX - ABS_MIN) as f32)) / 2.0;
    normalized.round() as i32
}

fn normalize_trigger_val(val: f32) -> i32 {
    let normalized = (val * ((ABS_MAX - ABS_MIN) as f32)).round() as i32 + ABS_MIN;
    normalized
}

// -----------------------------------------------------------------------------
// Interposer joystick configuration, sent when client connects.
// -----------------------------------------------------------------------------

#[repr(C)]
pub struct InterposerConfig {
    name: [u8; 255],
    vendor: u16,
    product: u16,
    version: u16,
    num_btns: u16,
    num_axes: u16,
    btn_map: [u16; MAX_BTNS],
    axes_map: [u8; MAX_AXES],
}

// -----------------------------------------------------------------------------
// Configuration types (analogous to STANDARD_XPAD_CONFIG in Python)
// -----------------------------------------------------------------------------

#[derive(Clone)]
pub struct XpadConfig {
    pub name: String,
    pub vendor: u16,
    pub product: u16,
    pub version: u16,
    pub btn_map: Vec<u16>,
    pub axes_map: Vec<u16>,
    pub mapping: MappingConfig,
}

#[derive(Clone)]
pub struct MappingConfig {
    // In this example the mapping uses simple HashMaps.
    pub axes_to_btn: HashMap<u8, Vec<u8>>,
    pub axes: HashMap<u8, u8>,
    pub btns: HashMap<u8, u8>,
    pub trigger_axes: Vec<u8>,
}

lazy_static::lazy_static! {
    pub static ref STANDARD_XPAD_CONFIG: XpadConfig = XpadConfig {
        name: "Selkies Controller".to_string(),
        vendor: 0x045e,
        product: 0x028e,
        version: 1,
        btn_map: vec![
            BTN_A, BTN_B, BTN_X, BTN_Y,
            BTN_TL, BTN_TR, BTN_SELECT, BTN_START,
            BTN_MODE, BTN_THUMBL, BTN_THUMBR,
        ],
        axes_map: vec![
            ABS_X, ABS_Y, ABS_Z, ABS_RX,
            ABS_RY, ABS_RZ, ABS_HAT0X, ABS_HAT0Y,
        ],
        mapping: MappingConfig {
            axes_to_btn: {
                let mut m = HashMap::new();
                m.insert(2, vec![6]);    // ABS_Z to L2
                m.insert(5, vec![7]);    // ABS_RZ to R2
                m.insert(6, vec![15, 14]); // ABS_HAT0X to DPad Left/Right
                m.insert(7, vec![13, 12]); // ABS_HAT0Y to DPad Down/Up
                m
            },
            axes: {
                let mut m = HashMap::new();
                m.insert(2, 3); // remap axis 2 to 3
                m.insert(3, 4); // remap axis 3 to 4
                m
            },
            btns: {
                let mut m = HashMap::new();
                m.insert(8, 6);
                m.insert(9, 7);
                m.insert(10, 9);
                m.insert(11, 10);
                m.insert(16, 8);
                m
            },
            trigger_axes: vec![2, 5],
        }
    };
}

// -----------------------------------------------------------------------------
// A simple wrapper for a UnixStream that also stores the client's word length.
// -----------------------------------------------------------------------------

pub struct InterposerSocket {
    pub stream: UnixStream,
    word_length: usize,
}

impl InterposerSocket {
    pub fn new(stream: UnixStream) -> Self {
        Self { stream, word_length: 8 }
    }

    pub fn set_word_length(&mut self, length: usize) {
        self.word_length = length;
    }

    pub fn word_length(&self) -> usize {
        self.word_length
    }

    pub async fn write_all(&mut self, buf: &[u8]) -> io::Result<()> {
        self.stream.write_all(buf).await
    }

    pub async fn read_exact(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        self.stream.read_exact(buf).await
    }

    pub async fn shutdown(&mut self) -> io::Result<()> {
        self.stream.shutdown().await
    }
}

// -----------------------------------------------------------------------------
// Event types and trait
// -----------------------------------------------------------------------------

pub trait Event {
    fn get_data(&self, word_len: usize) -> Vec<u8>;
}

// JS event structures
pub struct JSEvent {
    pub ts: u32,
    pub value: i16,
    pub event_type: u8,
    pub number: u8,
}

impl JSEvent {
    pub fn new(event_type: u8, number: u8, value: i16) -> Self {
        let ts = (SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() % 1000000000) as u32;
        Self { ts, value, event_type, number }
    }
}

impl Event for JSEvent {
    fn get_data(&self, _word_len: usize) -> Vec<u8> {
        let mut buf = BytesMut::with_capacity(8);
        buf.put_u32_le(self.ts);
        buf.put_i16_le(self.value);
        buf.put_u8(self.event_type);
        buf.put_u8(self.number);
        buf.to_vec()
    }
}

// EV event structures
pub struct EVEvent {
    pub ts_sec: i64,
    pub ts_usec: i64,
    pub event_type: u16,
    pub code: u16,
    pub value: i32,
}

impl EVEvent {
    pub fn new(event_type: u16, code: u16, value: i32) -> Self {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
        Self {
            ts_sec: now.as_secs() as i64,
            ts_usec: now.subsec_micros() as i64,
            event_type,
            code,
            value,
        }
    }
}

impl Event for EVEvent {
    fn get_data(&self, word_len: usize) -> Vec<u8> {
        let mut buf = BytesMut::with_capacity(32);
        if word_len == 8 {
            buf.put_i64_le(self.ts_sec);
            buf.put_i64_le(self.ts_usec);
            buf.put_u16_le(self.event_type);
            buf.put_u16_le(self.code);
            buf.put_i32_le(self.value);
            // Append a trailing SYN event.
            buf.put_i64_le(self.ts_sec);
            buf.put_i64_le(self.ts_usec);
            buf.put_u16_le(EV_SYN);
            buf.put_u16_le(SYN_REPORT);
            buf.put_i32_le(0);
        } else {
            buf.put_i32_le(self.ts_sec as i32);
            buf.put_i32_le(self.ts_usec as i32);
            buf.put_u16_le(self.event_type);
            buf.put_u16_le(self.code);
            buf.put_i32_le(self.value);
            buf.put_i32_le(self.ts_sec as i32);
            buf.put_i32_le(self.ts_usec as i32);
            buf.put_u16_le(EV_SYN);
            buf.put_u16_le(SYN_REPORT);
            buf.put_i32_le(0);
        }
        buf.to_vec()
    }
}

// -----------------------------------------------------------------------------
// Mapper traits and implementations
// -----------------------------------------------------------------------------

// Define a trait for mapping button/axis input to events.
pub trait GamepadMapper {
    fn get_btn_event(&self, btn_num: u8, btn_val: u8) -> Box<dyn Event + Send>;
    fn get_axis_event(&self, axis_num: u8, axis_val: i32) -> Box<dyn Event + Send>;

    fn get_mapped_btn(&self, config: &XpadConfig, btn_num: u8, btn_val: u8) -> Box<dyn Event + Send> {
        // (A simplified version: first check for a mapping in "btns")
        let mapped_btn = *config.mapping.btns.get(&btn_num).unwrap_or(&btn_num);
        if (mapped_btn as usize) >= config.btn_map.len() {
            error!("Button {} is out of range", mapped_btn);
            return self.get_btn_event(btn_num, btn_val);
        }
        self.get_btn_event(mapped_btn, btn_val)
    }

    fn get_mapped_axis(&self, config: &XpadConfig, axis_num: u8, axis_val: f32) -> Box<dyn Event + Send> {
        let mapped_axis = *config.mapping.axes.get(&axis_num).unwrap_or(&axis_num);
        if (mapped_axis as usize) >= config.axes_map.len() {
            error!("Axis {} is out of range", mapped_axis);
            return self.get_axis_event(axis_num, normalize_axis_val(axis_val));
        }
        self.get_axis_event(mapped_axis, normalize_axis_val(axis_val))
    }
}

// Constants for JS events.
const JS_EVENT_BUTTON: u8 = 0x01;
const JS_EVENT_AXIS: u8 = 0x02;

// JS Gamepad Mapper
pub struct JSGamepadMapper;

impl GamepadMapper for JSGamepadMapper {
    fn get_btn_event(&self, btn_num: u8, btn_val: u8) -> Box<dyn Event + Send> {
        Box::new(JSEvent::new(JS_EVENT_BUTTON, btn_num, btn_val as i16))
    }
    fn get_axis_event(&self, axis_num: u8, axis_val: i32) -> Box<dyn Event + Send> {
        Box::new(JSEvent::new(JS_EVENT_AXIS, axis_num, axis_val as i16))
    }
}

// EV Gamepad Mapper
pub struct EVGamepadMapper {
    config: XpadConfig,
}

impl EVGamepadMapper {
    pub fn new(config: XpadConfig) -> Self {
        Self { config }
    }
}

impl GamepadMapper for EVGamepadMapper {
    fn get_btn_event(&self, btn_num: u8, btn_val: u8) -> Box<dyn Event + Send> {
        let ev_code = self.config.btn_map.get(btn_num as usize).cloned().unwrap_or(0);
        Box::new(EVEvent::new(EV_KEY, ev_code, btn_val as i32))
    }
    fn get_axis_event(&self, axis_num: u8, axis_val: i32) -> Box<dyn Event + Send> {
        let ev_code = self.config.axes_map.get(axis_num as usize).cloned().unwrap_or(0) as u16;
        Box::new(EVEvent::new(EV_ABS, ev_code, axis_val))
    }
}

// -----------------------------------------------------------------------------
// The Gamepad server – one instance sends events over a Unix socket.
// -----------------------------------------------------------------------------

pub struct GamepadServer<M: GamepadMapper + 'static + Send + Sync> {
    pub js_index: u8,
    pub socket_path: String,
    pub config: XpadConfig,
    pub mapper: M,
    pub clients: Arc<Mutex<HashMap<u32, InterposerSocket>>>,
    pub event_sender: Sender<Box<dyn Event + Send>>,
}

impl<M: GamepadMapper + 'static + Send + Sync> GamepadServer<M> {
    pub fn new(
        js_index: u8,
        socket_path: String,
        config: XpadConfig,
        mapper: M,
        event_sender: Sender<Box<dyn Event + Send>>,
    ) -> Self {
        Self {
            js_index,
            socket_path,
            config,
            mapper,
            clients: Arc::new(Mutex::new(HashMap::new())),
            event_sender,
        }
    }

    // Build a configuration message for a new client.
    pub fn make_config(&self) -> InterposerConfig {
        let mut name_buf = [0u8; 255];
        let name_bytes = self.config.name.as_bytes();
        name_buf[..name_bytes.len()].copy_from_slice(name_bytes);

        let mut btn_map = [0u16; MAX_BTNS];
        for (i, &val) in self.config.btn_map.iter().enumerate() {
            btn_map[i] = val as u16;
        }

        // The input codes are all u16, but the config is u8, so convert.
        // This is consistent with the event spec.
        let mut axes_map = [0u8; MAX_AXES];
        for (i, &val) in self.config.axes_map.iter().enumerate() {
            axes_map[i] = val as u8;
        }

        let js_config = InterposerConfig {
            name: name_buf,
            vendor: self.config.vendor,
            product: self.config.product,
            version: self.config.version,
            num_btns: self.config.btn_map.len() as u16,
            num_axes: self.config.axes_map.len() as u16,
            btn_map,
            axes_map,
        };

        js_config
    }

    // Send configuration to a connected client.
    pub async fn setup_client(&self, mut client: InterposerSocket) -> io::Result<InterposerSocket> {
        info!("Sending config to client");
        let js_config = self.make_config();
        let size = mem::size_of::<InterposerConfig>();
        let buf: &[u8] = unsafe { std::slice::from_raw_parts(&js_config as *const InterposerConfig as *const u8, size) };
        client.write_all(&buf).await?;
        let mut buf = [0u8; 1];
        client.read_exact(&mut buf).await?;
        client.set_word_length(buf[0] as usize);
        Ok(client)
    }

    // Listen for new client connections.
    pub async fn run_server(&self) -> io::Result<()> {
        if Path::new(&self.socket_path).exists() {
            fs::remove_file(&self.socket_path)?;
        }
        let listener = UnixListener::bind(&self.socket_path)?;
        info!("Listening for connections on {}", self.socket_path);
        loop {
            match listener.accept().await {
                Ok((stream, _)) => {
                    let client = InterposerSocket::new(stream);
                    match self.setup_client(client).await {
                        Ok(client) => {
                            let fd = client.stream.as_raw_fd() as u32;
                            let word_length = client.word_length();
                            self.clients.lock().await.insert(fd, client);
                            info!("Client connected with fd: {}, word length: {}", fd, word_length);
                        }
                        Err(e) => {
                            warn!("Client setup failed: {}", e);
                        }
                    }
                }
                Err(e) => {
                    error!("Accept error: {}", e);
                    continue;
                }
            }
        }
    }

    // Background task that takes events from a channel and sends them to all clients.
    pub async fn send_events(&self, mut receiver: Receiver<Box<dyn Event + Send>>) {
        while let Some(event) = receiver.recv().await {
            let mut clients = self.clients.lock().await;
            let mut disconnected_fds = Vec::new();
            
            for (fd, client) in clients.iter_mut() {
                let data = event.get_data(client.word_length());
                if let Err(_) = client.stream.write_all(&data).await {
                    disconnected_fds.push(*fd);
                } else {
                    debug!("Sent event to client {}", fd);
                }
            }

            // Remove disconnected clients
            for fd in disconnected_fds {
                if let Some(mut client) = clients.remove(&fd) {
                    info!("Removing disconnected client {}", fd);
                    let _ = client.shutdown().await;
                }
            }
        }
    }

    // Convenience methods to enqueue a button or axis event.
    pub async fn send_btn(&self, btn_num: u8, btn_val: u8) {
        let event = self.mapper.get_mapped_btn(&self.config, btn_num, btn_val);
        let _ = self.event_sender.send(event).await;
    }

    pub async fn send_axis(&self, axis_num: u8, axis_val: f32) {
        let event = self.mapper.get_mapped_axis(&self.config, axis_num, axis_val);
        let _ = self.event_sender.send(event).await;
    }
}

// -----------------------------------------------------------------------------
// A "dual" gamepad server that creates both a JS and an EV server.
// -----------------------------------------------------------------------------

pub struct SelkiesGamepad {
    pub js_server: Arc<GamepadServer<JSGamepadMapper>>,
    pub ev_server: Arc<GamepadServer<EVGamepadMapper>>,
}

impl SelkiesGamepad {
    pub fn new(js_index: u8, js_socket_path: String, ev_socket_path: String) -> Self {
        let (js_tx, js_rx) = mpsc::channel::<Box<dyn Event + Send>>(100);
        let (ev_tx, ev_rx) = mpsc::channel::<Box<dyn Event + Send>>(100);

        let js_server = Arc::new(GamepadServer::new(
            js_index,
            js_socket_path,
            STANDARD_XPAD_CONFIG.clone(),
            JSGamepadMapper,
            js_tx,
        ));
        let ev_server = Arc::new(GamepadServer::new(
            js_index,
            ev_socket_path,
            STANDARD_XPAD_CONFIG.clone(),
            EVGamepadMapper::new(STANDARD_XPAD_CONFIG.clone()),
            ev_tx,
        ));

        {
            let js_server_clone = js_server.clone();
            tokio::spawn(async move {
                js_server_clone.send_events(js_rx).await;
            });
        }
        {
            let ev_server_clone = ev_server.clone();
            tokio::spawn(async move {
                ev_server_clone.send_events(ev_rx).await;
            });
        }

        Self { js_server, ev_server }
    }

    pub async fn run_server(&self) -> io::Result<()> {
        let js_server = self.js_server.clone();
        let ev_server = self.ev_server.clone();
        tokio::spawn(async move {
            let _ = js_server.run_server().await;
        });
        tokio::spawn(async move {
            let _ = ev_server.run_server().await;
        });
        Ok(())
    }

    pub async fn send_btn(&self, btn_num: u8, btn_val: u8) {
        self.js_server.send_btn(btn_num, btn_val).await;
        self.ev_server.send_btn(btn_num, btn_val).await;
    }

    pub async fn send_axis(&self, axis_num: u8, axis_val: f32) {
        self.js_server.send_axis(axis_num, axis_val).await;
        self.ev_server.send_axis(axis_num, axis_val).await;
    }
}

// -----------------------------------------------------------------------------
// Example main function using crossterm for keyboard input.
// -----------------------------------------------------------------------------

pub async fn run_gamepad_test() -> io::Result<()> {
    use crossterm::event::{read, Event as CEvent, KeyEvent, KeyCode};
    use std::time::Duration;
    use tokio::time::sleep;

    env_logger::init();

    info!("Starting standalone gamepad test");
    let js_index = 0;
    let js_socket_path = "/tmp/selkies_js0.sock".to_string();
    let ev_socket_path = "/tmp/selkies_event1000.sock".to_string();
    let gamepad = SelkiesGamepad::new(js_index, js_socket_path, ev_socket_path);

    info!("Starting server");
    gamepad.run_server().await?;

    let btn_keymap: HashMap<char, u8> = vec![
        ('z', 0),
        ('x', 1),
        ('a', 2),
        ('s', 3),
    ]
    .into_iter()
    .collect();

    let axis_keymap: HashMap<KeyCode, (u8, f32)> = vec![
        (KeyCode::Up, (7, -1.0)),
        (KeyCode::Down, (7, 1.0)),
        (KeyCode::Left, (6, -1.0)),
        (KeyCode::Right, (6, 1.0)),
    ]
    .into_iter()
    .collect();

    loop {
        if let CEvent::Key(KeyEvent { code, .. }) = read().unwrap() {
            if let Some(&(axis_num, axis_value)) = axis_keymap.get(&code) {
                gamepad.send_axis(axis_num, axis_value).await;
                info!("Axis Pressed: {:?} -> axis {}", code, axis_num);
                sleep(Duration::from_millis(50)).await;
                gamepad.send_axis(axis_num, 0.0).await;
                info!("Axis Released: {:?} -> axis {}", code, axis_num);
            } else if let CEvent::Key(KeyEvent { code: KeyCode::Char(c), .. }) = CEvent::Key(KeyEvent { 
                code, 
                modifiers: crossterm::event::KeyModifiers::empty(),
                kind: crossterm::event::KeyEventKind::Press,
                state: crossterm::event::KeyEventState::empty(),
            }) {
                if let Some(&btn_num) = btn_keymap.get(&c) {
                    gamepad.send_btn(btn_num, 1).await;
                    info!("Key Pressed: {} -> button {}", c, btn_num);
                    sleep(Duration::from_millis(50)).await;
                    gamepad.send_btn(btn_num, 0).await;
                    info!("Key Released: {} -> button {}", c, btn_num);
                }
            }
        }
    }
}

#[tokio::main]
pub async fn main() -> io::Result<()> {
    #[cfg(feature = "curses")]
    run_gamepad_test().await?;
    Ok(())
}
