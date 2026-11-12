"""Permite `python -m juez` sin instalar el paquete."""
import sys
from .cli import main


if __name__ == '__main__':
    sys.exit(main())
