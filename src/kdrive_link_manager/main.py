"""Application entry point."""

from tkinter import Tk

from .gui import LinkManagerApp


def main() -> None:
    root = Tk()
    LinkManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

