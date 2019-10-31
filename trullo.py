"""Trullo

usage:
    trl b [<board_shortcut>]
    trl l [<list_shortcut>]
    trl c <card_shortcut> [o | m <list_shortcut> | e]
    trl g <api_path>
    trl -h

    -h --help  this help message


commands:
    b [<board_shortcut>]
        shows the boards you can access
        with board_shortcut you can select the board you want to work with

    l [<list_shortcut>]
        shows the board you have currently selected
        with list_shortcut you can show a single list

    c <card_shortcut> [o | m <list_shortcut>]
        shows the card infos
        with o it opens the card shortUrl with your default application (launch xdg-open)
        with m and a target list you can move the card to that list

    g <api_path>
        make a direct api call adding auth params automatically (for debugging/hacking purpose)

env:
    you have to export this 2 variables to authenticate with trello:

    TRELLO_API_TOKEN - your trello api key
    TRELLO_TOKEN - a generated token

    you can obtain those values here: https://trello.com/app-key

"""
import os
import pprint
import subprocess
import tempfile

from docopt import docopt

from trullo.printer import Printer
from trullo.tclient import TClient

if __name__ == '__main__':
    args = docopt(__doc__, version='Trullo beta')

    tclient = TClient()

    selected_board_filepath = '/tmp/.trullo-selected-board'
    if os.path.exists(selected_board_filepath):
        with open(selected_board_filepath, 'r') as fh:
            selected_board_id, selected_board_name = fh.readline().split(' ', 1)

    if args['g']:
        api_path = args['<api_path>']
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(tclient.get(api_path))

    if args['b']:
        boards = tclient.get_boards()
        if args['<board_shortcut>']:
            board = [board for board in boards
                     if board.shortcut.lower().startswith(args['<board_shortcut>'])][0]
            print(f'selected board {board.raw_data["name"]}')
            with open(selected_board_filepath, 'w') as fh:
                fh.write(f'{board.id} {board.raw_data["name"]}')
        else:
            Printer.print_boards(boards)
            if os.path.exists(selected_board_filepath):
                print(f'\ncurrently selected board: {selected_board_name}')
            else:
                print(f'\nselect a board with `trl b <board_shortcut>`')

    # stuff that works only if a board is selected
    if not args['b'] and not os.path.exists(selected_board_filepath):
        print(f'first select a board with `trl b`')
        exit(1)

    if args['l']:
        board = tclient.get_board(selected_board_id)
        list_shortcut = args['<list_shortcut>']
        if list_shortcut:
            Printer.print_board(board, list_shortcut)
        else:
            Printer.print_board(board)

    if args['c']:
        board = tclient.get_board(selected_board_id)
        card_shortcut = args['<card_shortcut>']
        card = tclient.get_card([card.id for card in board.cards if card.shortcut.lower().startswith(card_shortcut)][0])

        open_command = args['o']
        move_command = args['m']
        edit_command = args['e']
        if open_command:
            subprocess.Popen(['xdg-open', card.raw_data['shortUrl']])
        elif move_command:
            target_list_shortcut = args['<list_shortcut>']
            list_id = [list_.id for list_ in board.lists if list_.id.lower().endswith(target_list_shortcut)][0]
            tclient.move_card(card.id, list_id)
        elif edit_command:
            tmpfile_path = f'{tempfile.gettempdir()}/trl-{card.id}'
            with open(tmpfile_path, 'w') as fd:
                clean_card_name = str(card.raw_data['name']).replace('\n', '')
                fd.writelines(
                    f"# The line below is the card title, lines after that are the card description\n"
                    f"{clean_card_name}\n\n{card.raw_data['desc']}")

            subprocess.Popen(['xdg-open', tmpfile_path]).wait()
            with open(tmpfile_path, 'r') as fd:
                lines = fd.readlines()
            tclient.edit_card(card.id,
                              lines[1].replace('\n', ''),
                              str.join('', lines[2:]))
        else:
            Printer.print_card(card)
