#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <linux/input.h>

void check_error(int result, const char *message)
{
    if (result < 0)
    {
        fprintf(stderr, "%s: %s\n", message, SDL_GetError());
        SDL_Quit();
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[])
{
    printf("Architecture sizeof input_event: %d bytes\n", sizeof(struct input_event));
    SDL_version compiled;
    SDL_version linked;

    // Get the version against which the program was compiled.
    SDL_VERSION(&compiled);
    // Get the version of the linked SDL library at runtime.
    SDL_GetVersion(&linked);

    printf("Compiled with SDL version %d.%d.%d\n",
           compiled.major, compiled.minor, compiled.patch);
    printf("Running with SDL version %d.%d.%d\n",
           linked.major, linked.minor, linked.patch);

    if (SDL_Init(SDL_INIT_JOYSTICK) < 0)
    {
        fprintf(stderr, "Failed to initialize SDL: %s\n", SDL_GetError());
        return EXIT_FAILURE;
    }

    printf("SDL initialized.\n");

    int num_joysticks = SDL_NumJoysticks();
    if (num_joysticks < 1)
    {
        printf("No joysticks connected.\n");
        SDL_Quit();
        return EXIT_SUCCESS;
    }

    printf("Number of joysticks found: %d\n", num_joysticks);

    SDL_Joystick *joystick = SDL_JoystickOpen(0);
    fprintf(stderr, "SDL_JoystickOpen response: 0x%lx\n", (long int)joystick);
    if (!joystick)
    {
        fprintf(stderr, "Could not open joystick: %s\n", SDL_GetError());
        SDL_Quit();
        return EXIT_FAILURE;
    }

    printf("Joystick opened: %s\n", SDL_JoystickName(joystick));

    // Get the joystick GUID.
    SDL_JoystickGUID guid = SDL_JoystickGetGUID(joystick);
    char guidStr[33];  // 32 hex digits plus null terminator.
    SDL_JoystickGetGUIDString(guid, guidStr, sizeof(guidStr));
    printf("Joystick GUID: %s\n", guidStr);
    
    // Print the vendor and product IDs in hexadecimal format.
    Uint16 vendor = SDL_JoystickGetVendor(joystick);
    Uint16 product = SDL_JoystickGetProduct(joystick);
    printf("Joystick Vendor ID: 0x%04X\n", vendor);
    printf("Joystick Product ID: 0x%04X\n", product);


    printf("Axes: %d\n", SDL_JoystickNumAxes(joystick));
    printf("Buttons: %d\n", SDL_JoystickNumButtons(joystick));
    printf("Hats: %d\n", SDL_JoystickNumHats(joystick));

    SDL_Event event;
    int running = 1;

    printf("Reading joystick input. Press Ctrl+C to quit.\n");

    while (running)
    {
        while (SDL_PollEvent(&event))
        {
            switch (event.type)
            {
            case SDL_JOYDEVICEADDED:
                printf("Saw device added event\n");
                break;

            case SDL_JOYAXISMOTION:
                printf("Axis %d moved to %d\n", event.jaxis.axis, event.jaxis.value);
                break;

            case SDL_JOYBUTTONDOWN:
                printf("Button %d pressed\n", event.jbutton.button);
                break;

            case SDL_JOYBUTTONUP:
                printf("Button %d released\n", event.jbutton.button);
                break;

            case SDL_JOYHATMOTION:
                printf("Hat %d moved to %d\n", event.jhat.hat, event.jhat.value);
                break;

            case SDL_QUIT:
                running = 0;
                break;

            default:
                printf("Unhandled input event type: 0x%x\n", event.type);
                break;
            }
        }

        SDL_Delay(10); // Add a small delay to prevent CPU overuse
    }

    SDL_JoystickClose(joystick);
    printf("Joystick closed.\n");
    SDL_Quit();
    return EXIT_SUCCESS;
}
