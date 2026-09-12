import math
import secrets
import string
import argparse

discard_chars = "il1Lo0O|"

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Secure Password Generator & Entropy Checker")
    parser.add_argument("-l", "--length", type=int, default=16, help="Password Length (min: 4, default: 16, max: 128)")
    parser.add_argument("-c", "--count", type=int, default=1, help="Generated Password Count (default:1, max: 10)")
    parser.add_argument("-a", "--no-ambiguous", action="store_true", default=True, help="Exclude Ambiguous Characters")
    args = parser.parse_args()
    return args

def get_length():
    while True:
        try:
            user_input = input("Password length (default 16): ").strip()
            if not user_input:
                length = 16
            else:
                length = int(user_input)
            if length < 4:
                print("Password must be at least 4 characters long")
                continue

            return length

        except ValueError:
            print("Invalid input. Please enter a number.")

def user_choices():
    exclude_ambiguous = input("Exclude ambiguous characters (y/n, default y): ").strip().lower()
    if not exclude_ambiguous:
        exclude_ambiguous = True
    elif exclude_ambiguous == "y":
        exclude_ambiguous = True
    elif exclude_ambiguous == "n":
        exclude_ambiguous = False
    else:
        print("Invalid input. Please enter y or n.")
        return user_choices()
    return exclude_ambiguous

def user_password_count():
    while True:
        try:
            user_input = input("Password count (default 1): ").strip()
            if not user_input:
                count = 1
            else:
                count = int(user_input)
            if count < 1:
                print("Password count must be at least 1.")
                continue
            return count
        except ValueError:
            print("Invalid input. Please enter a number.")



def get_charset(exclude_ambiguous=True):
    chars = string.ascii_letters + string.digits + string.punctuation

    if exclude_ambiguous:
        return ''.join(c for c in chars if c not in discard_chars)
    return chars


def pass_gen(length=16, exclude_ambiguous=True):
    try:
        pool = get_charset(exclude_ambiguous)
        sec_rand = secrets.SystemRandom()
        return ''.join(sec_rand.choices(pool, k=length))

    except Exception as e:
        print(f'Error {e}')

def pass_entropy(length=16, exclude_ambiguous=True):
    pool = get_charset(exclude_ambiguous)
    
    entropy = length * math.log2(len(pool))

    match entropy:
        case _ if entropy <= 30:
            strength = "Very Weak"
        case _ if entropy <= 60:
            strength = "Weak"
        case _ if entropy <= 90:
            strength = "Moderate"
        case _ if entropy <= 120:
            strength = "Strong"
        case _:
            strength = "Very Strong !!!"

    return strength

if __name__ == "__main__":
    args = parse_cli_args()
    
    for _ in range(args.count):
        print(f'{pass_gen(args.length, args.no_ambiguous)} - {pass_entropy(args.length, args.no_ambiguous)}')
