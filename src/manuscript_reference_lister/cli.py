import logging
import os
import sys
import traceback

import click

from .core import run
from .exceptions import JournalSyncError
from .logging_config import setup_logging
from .utils.config import get_config

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """CLI main entry point."""
    # Load config here at execution, not import
    ctx.ensure_object(dict)
    if "config" not in ctx.obj:
        ctx.obj["config"] = get_config()


@cli.command()
@click.pass_context
@click.option(
    "-f", "--input_file", type=str, default=None, help="Filepath to docx manuscript"
)
@click.option(
    "-t", "--text", type=str, default=None, help="Text to parse (can also be piped)"
)
@click.option(
    "-o",
    "--output_file",
    type=str,
    default=None,
    help="Filepath for the output Bibliography CSV",
)
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v (INFO), -vv (DEBUG))"
)
def main(ctx, input_file, text, output_file, verbose):
    """\b
    CLI entry point.
    Examples:
        # Process a file and specify output
        $ uv run python -m manuscript_reference_lister \
            --f "C:\\Documents\\manuscript.docx" -o "C:\\Documents\\bibliography.csv"

        Output file can be omitted, default generated file is \
            OUTPUT_DIR_PATH / "manuscript_references.csv"
        # Pipe source directly
        $ echo "Voila (Lenard et al., 2020)\r\nJournals\r\nNature Geoscience" | \
            uv run python -m manuscript_reference_lister
    """

    log_dir = setup_logging(verbose_level=verbose)

    logger.info("Starting manuscript-reference-lister...")
    logger.debug("Current working directory: %s", os.getcwd())
    logger.debug("Logs are being written to: %s", log_dir)

    if not text and not sys.stdin.isatty():
        # Read piped text with literal "\n" and "\r" converted into newline/CR bytes
        text = sys.stdin.read().strip().encode("utf-8").decode("unicode_escape")
        text = text.replace("\r", "")

    try:
        config = (ctx.obj or {}).get("config") or get_config()
        config.ensure_repo_directory()
        run(
            input_file_path=input_file,
            input_text=text,
            output_filepath=output_file,
            config=config,
        )
        click.echo("Done.")

    except click.ClickException as e:
        raise e

    except JournalSyncError as e:
        logger.warning("Pipeline halted: unfinished journal metadata mapping.")

        click.secho(
            f"\nError: {len(e.missing_journals)} journal(s) haven't been found.",
            fg="red",
            bold=True,
            err=True,
        )
        click.secho(
            "Please check the list and correct titles in the manuscript:\n",
            fg="red",
            err=True,
        )

        click.secho(
            f"{'input_title':<30} | suggested alternatives",
            fg="cyan",
            bold=True,
            err=True,
        )
        click.secho("-" * 70, fg="cyan", err=True)

        for title, alts in e.missing_journals.items():
            alternatives_str = "; ".join(alts) if alts else "No alternatives found"
            click.echo(f"{title:<30} | {alternatives_str}", err=True)

        click.echo("", err=True)
        sys.exit(1)

    except Exception as e:
        logger.critical(
            "Fatal application crash encountered during execution", exc_info=True
        )

        click.secho(f"\nError: An unexpected error occurred: {e}", fg="red", err=True)

        if verbose > 0:
            # If -v or -vv activated, traceback printed
            click.secho("\n--- Debug Traceback ---", fg="yellow", err=True)
            tb_lines = traceback.format_exception(type(e), e, e.__traceback__, limit=3)
            click.echo("".join(tb_lines), err=True)
            click.secho("-----------------------", fg="yellow", err=True)
        else:
            click.echo(
                "Use the '-v' or '-vv' option to see the full debug traceback.",
                err=True,
            )

        sys.exit(1)


if __name__ == "__main__":
    cli()
