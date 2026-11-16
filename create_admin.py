# Title : create_admin
# Author : Théo
# Description : CLI script to create a user of the admin page.
#               Usage : python create_admin.py <username>

import argparse
import getpass
import logging
import sys

from werkzeug.security import generate_password_hash

from database.writer import create_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s : %(message)s",
)
logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH: int = 12


def ask_password() -> str | None:
    """
    Ask the password twice in the terminal (nothing is displayed while typing).

    Args :
        None

    Return :
        The password (str), or None if it is too short or the two entries differ.
    """
    password: str = getpass.getpass("Password: ")

    if len(password) < MIN_PASSWORD_LENGTH:
        logger.error("Password too short (minimum %d characters)", MIN_PASSWORD_LENGTH)
        return None

    if password != getpass.getpass("Confirm password: "):
        logger.error("The two passwords are different")
        return None

    return password


def main() -> int:
    """
    Create an admin user in the database.

    Args :
        None

    Return :
        The exit code of the script (int): 0 if the user was created, else 1.
    """
    parser = argparse.ArgumentParser(description="Create a user for the admin page")
    parser.add_argument("username", help="login name of the new user")
    args = parser.parse_args()

    password = ask_password()
    if password is None:
        return 1

    # only the hash is stored, never the password
    user_id = create_user(args.username, generate_password_hash(password), "admin")
    if user_id is None:
        logger.error("User not created")
        return 1

    logger.info("User '%s' created (id=%d)", args.username, user_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
