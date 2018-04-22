import time
import pandas as pd
import twitter
from twitter import TwitterError
import sys

vars = [(i[0], i[1].replace('\n', '')) for i in [var.split('=') for var in open('envvars.txt').readlines()]]
api = twitter.Api(**dict(vars))


def ratelimiter(fn):
    def fndec(*args):
        try:
            return fn(*args)
        except TwitterError as e:
            if 'Rate limit' in e.message:
                mins = 15
                for m in range(mins):
                    t = m+1
                    time.sleep(60*t)
                    print "Sleeping for {} more minutes...".format(mins-t)
        return fn(*args)
    return fndec


@ratelimiter
def get_tweets(hashtag, count):
    return api.GetSearch(raw_query='q=%23{}&count={}&result_type=mixed'.format(hashtag, count))


@ratelimiter
def get_id(tweet):
    return tweet.AsDict()['id']


@ratelimiter
def get_retweeters(id):
    return api.GetRetweeters(status_id=id)


@ratelimiter
def get_screen_name(userid):
    return api.GetUser(user_id=userid).AsDict()['screen_name']


def main(hashtag, count, filter_empty=False):
    tweets = get_tweets(hashtag, count)
    retweeters = [get_retweeters(id) for id in [get_id(tweet) for tweet in tweets]]
    mapping = [(tweets[i].AsDict()['user']['id'], retweeters[i]) for i in range(len(tweets))]
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

    df = pd.DataFrame.from_records(res)
    df = df[['tweeter', 'retweeter']]
    if filter_empty:
        df = df[df['retweeter'] != '']
    df.to_csv('results.csv', index=False)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        hashtag, count, filter_empty = open('args.txt').readline().split(' ')
    elif len(sys.argv) != 4:
        print "USAGE: python app.py <hashtag> <# of tweets> <filter results w/o retweets (True or False)>"
        sys.exit(1)
    else:
        hashtag, count, filter_empty = sys.argv[1], sys.argv[2], bool(sys.argv[3])
    main(hashtag, count, filter_empty)
