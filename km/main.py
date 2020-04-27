import click
import subprocess
import requests
from diskcache import Cache

from pathlib import Path

@click.command()
@click.option('--source')
@click.option('--clear-cache', is_flag=True)
@click.option('--update', is_flag=True)
def main(source, clear_cache, update):

    if clear_cache and update:
        raise NotImplementedError

    clear_cache = clear_cache or update

    km_dir_path = '/tmp/km'
    km_dir_path_object = Path(km_dir_path)
    km_dir_path_object.mkdir(exist_ok=True)

    cache_dir_path = '/tmp/km/cache'
    cache = Cache(cache_dir_path)

    if clear_cache:
        cache.clear()
        print('Cache cleared')
        return True
    
    if source:
        if 'github.com' in source and 'blob' in source:
            url = source.replace('blob', 'raw')
        else:
            url = source
    else:
        url = 'https://github.com/commmands/commands/raw/master/commands_1.commands'
        
    cache_value = cache.get(url)

    temp_commands_path = '/tmp/km/temp_commands'
    temp_commands_path_object = Path(temp_commands_path)
    temp_commands_path_object.parent.mkdir(parents=True, exist_ok=True)

    if cache_value:
        temp_commands_path_object.write_text(cache_value)
    else:
        commands_response = requests.get(url)
        print(f'Getting: {url}')
        commands = commands_response.text
        temp_commands_path_object.write_text(commands)
        cache.set(url, commands, expire=86400)

    perl_part = "perl -e 'ioctl STDOUT, 0x5412, $_ for split //, do{ chomp($_ = <>); $_ }'"
    command = f"cat {temp_commands_path} | fzf --tac | {perl_part} ; echo"

    subprocess.call(command, shell=True)
