#!/usr/bin/env python3

# Import socket module 
import socket
import os
from time import sleep

from multiprocessing import Process, Queue
import queue


################################
# Print help functions
################################

def clear_screen():
    """ Clear terminal screen """
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        pass

def clear_line():
    """ Clear line """
    print(f"\033[K", end='')

def prev_line():
    """ Move cursor to previous line """
    print(f"\033[F", end='')


def draw_dices(dice_values):
    tlines,blines,top, middle, bottom = [],[],[],[],[]
    #  = []
    # bottom = []
    line    = " --- "
    blank   = "|   |"
    double  = "|O O|"
    right   = "|  O|"
    center  = "| O |"
    left    = "|O  |"
    for dice in dice_values:
        tlines.append(line)
        blines.append(line)
        if dice in (6, 5, 4):
            top.append(double)
            bottom.append(double)
            if dice == 6:
                middle.append(double)
                continue
        elif dice in (3, 2):
            top.append(right)
            bottom.append(left)
        if dice in (5, 3, 1):
            middle.append(center)
            if dice == 1:
                top.append(blank)
                bottom.append(blank)
                continue
        elif dice in (4, 2):
            middle.append(blank)
    # draw
    top_string = ' '.join(top)
    middle_string = ' '.join(middle)
    bottom_string = ' '.join(bottom)
    tlines_string = ' '.join(tlines)
    blines_string = ' '.join(blines)
    print(f"{tlines_string}")
    print(f"{top_string}")
    print(f"{middle_string}")
    print(f"{bottom_string}")
    print(f"{blines_string}")



def get_response(s):
    response = s.recv(1024)
    return str(response.decode('ascii')).split('\x01')



################################
# Network communication
################################

def server_incoming(s, comm_queue):
    """ Get messages from server one at a time """
    while True:
        messages = get_response(s)
        if messages:
            for message in messages:
                comm_queue.put(message)
                if message == "EXIT":
                    return
        else:
            print("Break server")
            break
        sleep(0.5)

def get_next_message_from_queue(comm_queue):
    while True:
        try:
            data = comm_queue.get_nowait()
        except queue.Empty:
            sleep(0.1)
        else:
            return data    




################################
# Player events
################################

def throw(s):
    input(">> Kast terningerne! Tryk [enter]")
    s.send("OK".encode('ascii'))
    prev_line()
    clear_line()

def confirm(s):
    answer = input("Tror du på sidste bud? (ja/nej) : ")
    if answer == "ja" or not answer:
        s.send("OK".encode('ascii'))
    else:
        s.send("CHEAT".encode('ascii'))
    prev_line()
    clear_line()


def new_game(s):
    answer = input("Spil igen? (ja/nej) : ")
    if answer == "ja" or not answer:
        s.send("OK".encode('ascii'))
    else:
        s.send("QUIT".encode('ascii'))


def guess(s,comm_queue):
    guess_accepted = False
    user_msg = "Din tur. Afgiv dit bud: "
    while not guess_accepted:
        g = input(user_msg)
        if not g:
            user_msg = "Mangler bud. Prøv igen: "
            continue
        msg = "OK;"+g
        s.send(msg.encode('ascii'))
        guess_again = False
        while not guess_again:
            r = get_next_message_from_queue(comm_queue)
            if r == "OK":
                guess_accepted = True
                guess_again = True
                prev_line()
                clear_line()
            elif r == "GUESS":
                user_msg = "Forkert bud. Prøv igen: "
                guess_again = True
            else:
                try:
                    message = r.split(';', 2)
                    if message[0] == "MSG":
                        print(message[1])
                except:
                    pass
            sleep(0.5)

def get_name():
    """
    Input player name
    """
    name = input("Indtast spillernavn (max. 32 tegn): ")
    if len(name) > 32:
        name = name[:32]
    return name


################################
# Game functions
################################

def create_game(s, comm_queue):
    correct_number_of_players = False
    while not correct_number_of_players:
        number_of_players = input("Angiv antal af spillere (2-16): ")
        try:
            nop = int(number_of_players)
            if nop < 16 and nop > 1:
                correct_number_of_players = True
        except:
            print("(Et tal mellem 2 og 16...)")
    
    print("Venter på spillere...")
        
    CREATE = f"CREATE;{number_of_players}"
    s.send(CREATE.encode('ascii'))

    while True:
        response = get_next_message_from_queue(comm_queue)
        if response == "OK":
            break
        sleep(1)

    start_game(s, comm_queue)


def start_game(s, comm_queue):
    game_over = False
    first_message = True
    while not game_over:
        command = get_next_message_from_queue(comm_queue)
        if command == "EXIT":
            print("Bye!")
            game_over = True
        elif command == "THROW":
            throw(s)
        elif command == "GUESS":
            guess(s, comm_queue)
        elif command == "CONFIRM":
            confirm(s)
        elif command == "NEW_GAME":
            new_game(s)
        else:
            try:
                message = command.split(';', 2)
                if message[0] == "MSG":
                    if first_message:
                        first_message = False
                        clear_screen()
                    print(message[1])
                elif message[0] == "DICE":
                    dices = [int(x) for x in message[1].split()]
                    print()  # new line
                    draw_dices(dices)
            except:
                pass


################################
# Main
################################

def Main(): 
    # input server IP-address
    host = input("Indtast game-server IP-adresse: ")
    if not host:
        # local host IP '127.0.0.1'
        host = '127.0.0.1'

    # get player name
    player_name = get_name()
  
    # Define the port on which you want to connect 
    port = 12345
  
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  
    # connect to server on local computer
    try:
        s.connect((host,port))
    except ConnectionRefusedError:
        print("Server ikke klar. Prøv igen senere.")
        s.close()
        return
  
    # setup communication channel
    comm_queue = Queue()
    comm_channel = Process(target=server_incoming, args=(s, comm_queue))
    comm_channel.start()

    # message you send to server 
    STARTGAME = f"{player_name}"

    # message sent to server 
    s.send(STARTGAME.encode('ascii'))

    # message received from server
    data = get_next_message_from_queue(comm_queue)

    if data == "NEW":
        # no game exists. Create new game
        create_game(s, comm_queue)
    elif data == "OK":
        print("Venter på sidste spillere...")
        start_game(s, comm_queue)

    comm_channel.join()

    # close the connection 
    s.close() 
  

if __name__ == '__main__': 
    Main()
