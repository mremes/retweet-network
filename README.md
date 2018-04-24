# Social network analysis crawler
This is a Python 2.7 app for fetching tweeter-retweeter relationships based on a hashtag.

## Usage
Run the script like: `python app.py <hashtag> <# of tweets> <separator> <language code> <filter not retweeted (True or False)>` and it will output a `results.csv` file containing data like:
```
tweeter,retweeter
user1,user2
...
```

Thou can also put arguments into `args.txt` file (for Windows user convenience)
