import click
import subprocess
import validators
import requests
from diskcache import Cache

from pathlib import Path


@click.command()
@click.option("--source", "source_param")
@click.option("--clear-cache", is_flag=True)
@click.option("--update", is_flag=True)
def main(source_param, clear_cache, update):

    if clear_cache and update:
        raise NotImplementedError

    clear_cache = clear_cache or update

    km_dir_path = "/tmp/km"
    km_dir_path_object = Path(km_dir_path)
    km_dir_path_object.mkdir(exist_ok=True)

    cache_dir_path = "/tmp/km/cache"
    cache = Cache(cache_dir_path)

    if clear_cache:
        cache.clear()
        print("Cache cleared")
        return True

    if source_param:
        is_url = validators.url(source_param)
        is_file = Path(source_param).exists()

        if is_url:
            if "github.com" in source_param and "blob" in source_param:
                source = source_param.replace("blob", "raw")
            else:
                source = source_param
        elif is_file:
            source = source_param
        else:
            raise NotImplementedError
    else:
        # Default source
        km_dir_path_object = Path.home().joinpath(".km")
        source = str(km_dir_path_object.joinpath("default.commands"))

    cache_value = cache.get(source)

    temp_commands_path = "/tmp/km/temp_commands"
    temp_commands_path_object = Path(temp_commands_path)
    temp_commands_path_object.parent.mkdir(parents=True, exist_ok=True)

    if cache_value:
        temp_commands_path_object.write_text(cache_value)
    else:
        is_url = validators.url(source)
        is_file = Path(source).exists()

        if is_url:
            commands_response = requests.get(source)
            commands = commands_response.text
        elif is_file:
            commands = Path(source).read_text()
        else:
            raise NotImplementedError

        # Generate full commands with 'includes'

        full_commands_text = _get_full_commands_text(commands)
        import os

        full_commands_text_without_empty_lines = os.linesep.join(
            [s.strip() for s in full_commands_text.splitlines() if s]
        )

        final_commands = full_commands_text_without_empty_lines

        temp_commands_path_object.write_text(final_commands)
        cache.set(source, final_commands, expire=86400)

    perl_part = (
        "perl -e 'ioctl STDOUT, 0x5412, $_ for split //, do{ chomp($_ = <>); $_ }'"
    )
    command = f"cat {temp_commands_path} | fzf --tac | {perl_part} ; echo"

    subprocess.call(command, shell=True)


def _get_full_commands_text(commands_text):

    lines = commands_text.split("\n")

    new_lines = []

    for line in lines:

        if line.startswith("#include"):
            source = line.split("#include ")[1]
            source_text = _get_source_text(source)
            source_lines = source_text.split("\n")
            new_lines += source_lines

        else:
            new_lines.append(line)

    # Remove multiple new lines from the end of the file
    reversed_new_lines = list(reversed(new_lines))
    for index, line in enumerate(reversed_new_lines):
        if line.strip() == "" and reversed_new_lines[index + 1].strip() == "":
            reversed_new_lines.pop(index)
        else:
            break

    new_lines = list(reversed(reversed_new_lines))

    full_text = "\n".join(new_lines)

    return full_text


def _get_source_text(source):

    is_url = validators.url(source)
    is_file = Path(source).exists()

    if is_url:
        commands_response = requests.get(source)
        text = commands_response.text
    elif is_file:
        text = Path(source).read_text()
    else:
        print("Source is not a url or a file path")
        raise click.Abort

    return text
