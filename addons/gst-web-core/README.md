# GST Web Core

The purpose of this code is to be the core of the frontend and what we use as a base layer of application logic in a web browser. 

The core web library has to be simple to use from even CDNs, this is designed to only have the user define an app div and embedd the script, this is all that is required: 

```
<!DOCTYPE html>
<html>
<body>
  <div id="app"></div>
  <script type="module" src="selkies-core.js"></script>
</body>
</html>
```

# Building

This can be built into a single `selkies-core.js` file that can be embedded using [vite](https://vite.dev/) simply: 

```
npm install
npm run build
```

The development server with hot reloading can be started with `npm serve`. 

# Development and message bus

The core application is simple because it does not render any menus or handle anything outside of the remote display logic, projects external to this will need to use the messaging bus to listen for messages like: 

* Current status
* Logs
* Load statistics

And will need to send messages to modify settings.

## Message bus exposed settings and data

WIP WIP WIP WIP WIP WIP
