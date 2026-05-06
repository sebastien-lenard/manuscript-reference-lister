import logging
import os
import sys

import click

from .core import run


@click.command()
@click.option(
    "-f", "--input_file", type=str, default=None, help="Filepath to docx manuscript"
)
@click.option(
    "-t", "--text", type=str, default=None, help="Text to parse (can also be piped)"
)
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v (INFO), -vv (DEBUG))"
)
def main(input_file, text, verbose):
    """\b
    CLI entry point.
    Examples:
        # Pass source via flag
        $ uv run python -m src.manuscript_reference_lister --file "manuscript.docx"

        # Pipe source directly
        $ echo "Voila (Lenard et al., 2020)\r\nJournals\r\nNature Geoscience" | \
            uv run python -m src.manuscript_reference_lister
    """

    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    log_level = levels.get(verbose, logging.DEBUG)
    logging.basicConfig(
        level=log_level, format="%(levelname)s [%(name)s]: %(message)s", force=True
    )

    click.echo("Starting manuscript-reference-lister...")
    click.echo(f"Current directory: {os.getcwd()}")

    if not text and not sys.stdin.isatty():
        # Read piped text with literal "\n" and "\r" converted into newline/CR bytes
        text = sys.stdin.read().strip().encode("utf-8").decode("unicode_escape")
        text = text.replace("\r", "")

    run(input_file_path=input_file, input_text=text)

    click.echo("Done.")


if __name__ == "__main__":
    main()
