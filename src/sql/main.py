import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from orm import ORM


def main():
    ORM.create_tables()

if __name__ == "__main__":
    main()

