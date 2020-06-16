import json
import os

from pathlib import Path
from re import match
from shlex import split
from subprocess import CalledProcessError
from subprocess import PIPE
from subprocess import Popen as Proc
from subprocess import run as runProc
from typing import ByteString
from typing import List
from typing import Tuple


def prepare_fixtures_for(spider_paths: List[Path], fixtures_dir: Path, fixture_type: str) -> None:
    """
    This function takes a list of spiders--e.g spiders targeting the "commissary/"--and produces a formatted list of fixtures.
    It's purpose is to generate structs that represent an "inmate" against which spider tests can be written.
    Steps to perform this feat are three-fold:
        1. generate raw spider output
        2. formate that output
        3. persist the formatted output

    TODO (withtwoemms) -- use concurrent.futures to better handle multiple spiders
    """
    # Validation
    if not all(path.exists() for path in spider_paths + [fixtures_dir]):
        raise ValueError(f'The output directory, "{fixtures_dir}", and all spiders from which to create fixtures must already exist.')
    if not fixture_type in ['json']:
        raise ValueError(f'Currently, "{fixture_type}" is not supported.')


    print('\nGenerating fixtures for:')
    for spider_path in spider_paths:
        print(f'....{spider_path}')
        spider_fixture_path = fixtures_dir.joinpath(f'{spider_path.stem}.{fixture_type}')
        spider_fixture_path.write_text('')

        # STEP 1: leverage scrapy to generate some raw output
        fixture_generation_command = split(f'scrapy runspider --set=ROBOTSTXT_OBEY=False {str(spider_path)} -o {str(spider_fixture_path)}')
        runProc(fixture_generation_command, stderr=PIPE)  # NOTE: PIPE used to stash what would flow to stdout

        # STEP 2: format and truncate that output
        gotten_contents = runProc(split(f'cat {str(spider_fixture_path)}'), stdout=PIPE).stdout.decode('utf-8')
        contents_dict = json.loads(gotten_contents)  # NOTE: raw output is truncated
        formatted_json = runProc(split('jq .'), stdout=PIPE, input=json.dumps(contents_dict[-5:]).encode())

        # STEP 3: write the formatted output to disk
        spider_fixture_path.write_text(formatted_json.stdout.decode('utf-8'))


test_spiders_dir = 'tests/scraper/spiders'
test_fixtures_dir = Path('tests/fixtures')
test_spiders = [Path(os.path.join(test_spiders_dir, file)) for file in os.listdir(test_spiders_dir)
    if file.endswith('.py')
    and not match(r'__.+__\.py', file)]


def prepare_fixtures():
    prepare_fixtures_for(
        spider_paths=test_spiders,
        fixtures_dir=test_fixtures_dir,
        fixture_type='json'
    )
