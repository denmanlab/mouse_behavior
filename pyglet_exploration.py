import imgui
from imgui.integrations.pyglet import create_renderer
import pyglet

# Initialize ImGui context
imgui.create_context()

window = pyglet.window.Window(width=800, height=600, caption="Experiment Settings")
imgui_renderer = create_renderer(window)

# Default settings
settings = {
    "reward_volume": 10,
    "min_iti": 1,
    "max_iti": 20,
    "min_wait_time": 1,
    "max_wait_time": 20
}

@window.event
def on_draw():
    window.clear()
    imgui.new_frame()

    # Begin a new ImGui window
    imgui.begin("Settings", True, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

    # Sliders for settings
    for setting in settings:
        changed, new_value = imgui.slider_int(f"{setting.replace('_', ' ').title()}", settings[setting], 1, 100 if setting == "reward_volume" else 20, "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
        if changed:
            settings[setting] = new_value
            print(f"{setting}: {settings[setting]}")

    # Make sure the min/max settings are logically consistent
    settings["max_iti"] = max(settings["min_iti"], settings["max_iti"])
    settings["max_wait_time"] = max(settings["min_wait_time"], settings["max_wait_time"])

    imgui.end()

    imgui.render()
    imgui_renderer.render(imgui.get_draw_data())

@window.event
def on_close():
    imgui_renderer.shutdown()

if __name__ == "__main__":
    pyglet.app.run()


