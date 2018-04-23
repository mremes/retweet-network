import time
import pandas as pd
import twitter
from twitter import TwitterError
import sys

vars = [(i[0], i[1].replace('\n', '')) for i in [var.split('=') for var in open('envvars.txt').readlines()]]
api = twitter.Api(**dict(vars))


def handle_ratelimit(e):
    print "Rate limit hit!"
    mins = 15
    for m in range(mins):
        print "Sleeping for {} more minutes...".format(mins)
        time.sleep(60)
        mins -= 1


def ratelimiter(fn):
    def fndec(*args):
        try:
            return fn(*args)
        except TwitterError as e:
            handle_ratelimit(e)
        return fn(*args)
    return fndec


@ratelimiter
def get_tweets(hashtag, count, lang):
    try:
        return api.GetSearch(raw_query='q=%23{}&count={}&lang={}&result_type=mixed'.format(hashtag, count, lang))
    except TwitterError as e:
        handle_ratelimit(e)
        return api.GetRetweeters(status_id=id)


@ratelimiter
def get_id(tweet):
    return tweet.AsDict()['id']


@ratelimiter
def get_retweeters(id):
    try:
        return api.GetRetweeters(status_id=id)
    except TwitterError as e:
        handle_ratelimit(e)
        return api.GetRetweeters(status_id=id)


@ratelimiter
def get_screen_name(userid):
    try:
        return api.GetUser(user_id=userid).AsDict()['screen_name']
    except TwitterError as e:
        handle_ratelimit(e)
        return api.GetRetweeters(status_id=id)


def main(hashtag, count, separator, lang, filter_empty=False):
    print "Hashtag: {}, count: {}, separator: {}, filter empty retweets: {}".format(hashtag,
                                                                                    count,
                                                                                    separator,
                                                                                    filter_empty)
    print "Fetching tweets..."
    tweets = get_tweets(hashtag, count, lang)
    print "Fetching retweeters..."
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
    print "Creating a CSV..."
    df = pd.DataFrame.from_records(res)
    df = df[['tweeter', 'retweeter']]
    if filter_empty:
        df = df[df['retweeter'] != '']
    df.to_csv('results.csv', index=False, sep=separator)
    print "DONE :-)"


if __name__ == '__main__':
    if len(sys.argv) == 1:
        hashtag, count, separator, lang, filter_empty = open('args.txt').readline().split(' ')
    elif len(sys.argv) != 5:
        print "USAGE: python app.py <hashtag> <# of tweets> <separator> <language code> <filter results w/o retweets (True or False)>"
        sys.exit(1)
    else:
        hashtag, count, separator, lang, filter_empty = sys.argv[1], sys.argv[2], sys.argv[3], bool(sys.argv[4]), sys.argv[5]
    main(hashtag, count, separator, lang, filter_empty)
