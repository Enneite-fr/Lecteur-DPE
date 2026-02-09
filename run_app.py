from nicegui import ui
import src.nice_ui # To ensure the page is registered

if __name__ in {"__main__", "__mp_main__"}:
    # native=True would open in a window, but standard browser is often preferred for local web tools
    # user requested: "le programme ouvre une page web pour l'interaction"
    ui.run(title="Lecteur DPE", port=8080, reload=True)
