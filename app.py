from __future__ import print_function

import functools
import time
import pandas as pd
import twitter
from twitter import TwitterError
import sys
import math


def print_magic(printstr, intv=.03, end='\n'):
    for c in printstr:
        print(c, end='')
        sys.stdout.flush()
        time.sleep(intv)
    print('', end=end)

print_magic("""
####    RetweetNetwork - Twitter Data Utility   ####
####           Author: Matti Remes              ####
####              remes@iki.fi                  ####
####    github.com/mremes/retweetnetwork        ####
""", 0.005)


vars = [(i[0], i[1].replace('\n', '')) for i in [var.split('=') for var in open('envvars.txt').readlines()]]
api = twitter.Api(**dict(vars))


def handle_ratelimit(e):
    mins = 15
    for m in range(mins * 60):
        sys.stdout.flush()
        sys.stdout.write("\rRate limit hit! Sleeping for {} more seconds...".format(str(mins * 60 - m)).rjust(3))
        time.sleep(1)


def rate_limiter(fn):
    @functools.wraps(fn)
    def fndec(*args):
        while True:
            try:
                return fn(*args)
            except TwitterError as e:
                handle_ratelimit(e)
                continue
    return fndec


@rate_limiter
def fetch_tweets(hashtag, count, lang, max_id):
    query = 'q=%23{}&count={}&lang={}&result_type=mixed'.format(hashtag, count, lang)
    if max_id:
        query += '&max_id={}'.format(max_id)
    time.sleep(5)
    return api.GetSearch(raw_query=query)


@rate_limiter
def get_tweets(hashtag, count, lang):
    max_iter = 200
    cur_iter = 0
    tweets = []
    last3len = [-1, -1, -1]
    max_id = None
    while len(tweets) < count and cur_iter < max_iter:
        last3len[cur_iter % 3] = len(tweets)
        if len(set(last3len)) == 1:
            print("Done.")
            break
        sys.stdout.flush()
        res = fetch_tweets(hashtag, min(count, 100), lang, max_id)
        max_id = min([t.AsDict()['id'] for t in res])
        tweets += res
        cur_iter += 1
        sys.stdout.write("\r{} / {} tweets fetched...".format(str(len(tweets)).rjust(int(math.log10(count))), count))
        time.sleep(1)
    print('\n')
    return tweets


@rate_limiter
def get_id(tweet):
    return tweet.AsDict()['id']


@rate_limiter
def get_retweeters(id):
    return api.GetRetweeters(status_id=id)


@rate_limiter
def get_screen_name(userid):
    return api.GetUser(user_id=userid).AsDict()['screen_name']


def get_tweeter_retweeter_mapping(tweets, retweeters):
    return [(tweets[i].AsDict()['user']['id'], retweeters[i])
            for i in range(len(tweets))]


def get_records(mapping):
    res = []
    for m in mapping:
        tweeter = get_screen_name(m[0])
        retweeters = []
        for rt in m[1]:
            retweeter = get_screen_name(rt)
            retweeters.append(retweeter)
        if len(retweeters) == 0:
            res.append({'tweeter': tweeter, 'retweeter': ''})
        else:
            res += [{'tweeter': tweeter, 'retweeter': retweeter} for retweeter in retweeters]
    return res


def main(hashtag, count, separator, lang, filter_empty=False, output_file='results.csv'):
    print("Hashtag: {}, count: {}, separator: {}, filter empty retweets: {}".format(hashtag,
                                                                                    count,
                                                                                    separator,
                                                                                    filter_empty))

    while True:
        print_magic("DO YOU WANT TO USE THESE VALUES? (Y/N)", end=' ')
        answ = raw_input().lower()
        print('')
        if answ not in ['n', 'y']:
            continue
        elif answ == 'n':
            vars = ['hashtag', 'count', 'separator', 'lang', 'filter_empty', 'output_file']
            questions = ['Hashtag of a tweet',
                         'How many tweets',
                         'How do you want to separate the data',
                         'Language of a tweet',
                         'Do you want to filter results without retweets (True/False)',
                         'Where do you want to save the CSV file?']
            types = [str, int, str, str, bool, str]
            for i in range(len(vars)):
                print('{} ({}): '.format(questions[i], locals()[vars[i]]), end='')
                answ = raw_input()
                if not len(answ) == 0:
                    exec('{} = {}("{}")'.format(vars[i], types[i].__name__, answ))
        break

    print("Fetching tweets...\n")
    tweets = get_tweets(hashtag, count, lang)
    print("Fetching retweeters\n")
    retweeters = [get_retweeters(twid) for twid in [get_id(tweet) for tweet in tweets]]
    print("Creating tweeter-retweeters mapping...")
    mapping = get_tweeter_retweeter_mapping(tweets, retweeters)
    print("Creating result records...")
    records = get_records(mapping)

    print("Creating a CSV...")
    df = pd.DataFrame.from_records(records)
    df = df[['tweeter', 'retweeter']]
    df = df[df['retweeter'] != ''] if filter_empty else df
    df.to_csv(output_file, index=False, sep=separator)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        hashtag, count, separator, lang, filter_empty = open('args.txt').readline().split(' ')
    elif len(sys.argv) != 5:
        print("""
        USAGE:
        python app.py <hashtag> <# of tweets> <separator> <lang code> <filter w/o retweets (True or False)>
        """)
        sys.exit(1)
    else:
        hashtag, count, separator, lang, filter_empty = sys.argv[1], sys.argv[2], sys.argv[3], \
                                                        bool(sys.argv[4]), sys.argv[5]
    main(hashtag, int(count), separator, lang, filter_empty)
