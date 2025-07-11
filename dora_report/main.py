from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    
    arguments = parser.parse_args()
    print(arguments)
 
if __name__ == "__main__":
    main()