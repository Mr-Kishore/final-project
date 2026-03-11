"""GUI components for Conversational Data Analysis System."""

__all__ = ['streamlit_main', 'main']

def streamlit_main():
    """Entry point for Streamlit UI."""
    from .streamlit_app import main
    main()

def main():
    """Entry point for desktop GUI."""
    from .app import main as app_main
    app_main()
