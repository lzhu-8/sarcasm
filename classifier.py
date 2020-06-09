import json
import csv
import sys
import getopt
import os
import math
import operator
from nltk.tokenize import TweetTokenizer 
from collections import defaultdict
import random
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score


# reads items in json file as a list of dicts, where the entries are "article_link", "headline", "is_sarcastic"
def read_headlines(filename = 'data/headlines/Sarcasm_Headlines_Dataset.json'):
    artList = []
    with open(filename) as f:
        for jsonObj in f:
            art = json.loads(jsonObj)
            artList.append(art)
    return artList

def naive_headlines(articles=read_headlines()):
    artlist = {}
    for art in articles:
        artlist[art["headline"]] = art["is_sarcastic"]
    return artlist

# extract tweets as dict mapping tweet to sarcasm = 1, not sarcasm = 0 
def read_tweets(filename = 'data/twitter/sarcasm-dataset.txt'):
    tweetlist = {}
    with open(filename, 'r') as fp:
        for twt in fp:
            tweetlist[twt[0:len(twt)-2].strip()] = twt[-2]
    return tweetlist

# returns json file as dict
def read_reddit(filename = 'data/reddit/comments.json'):
    with open(filename) as f:
        for jsonObj in f:
            c = json.loads(jsonObj)
    return c

def read_reddit_label(filename = 'data/reddit/train-balanced.csv'):
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        lab = {}
        for row in csv_reader:
            line_count+=1
            sp = row[0].split('|')
            for i,s in enumerate(sp[1].split()):
                lab[s] = int(sp[2].split()[i])
        print(f'Processed {line_count} lines.')
        return lab

class NaiveBayes:
    class tsplit:
        """Represents a set of training/testing data. self.train is a list of Examples, as is self.dev and self.test. 
        """
        def __init__(self):
            self.train = []
            self.dev = []
            self.test = []

    class instance:
        """Represents a document with a label. klass is 'sarcastic' or 'not' by convention.
             words is a list of strings.
        """
        def __init__(self):
            self.klass = ''
            self.words = []

    def __init__(self):
        """NaiveBayes initialization"""
        self.USE_BIGRAMS = False
        self.BEST_MODEL = False

        self.not_docs = 0
        self.sarcasm_docs = 0
        self.total_docs = 0

        # unigrams
        self.words_sarcasm = defaultdict(int)
        self.words_not = defaultdict(int)
        self.vocab = set()
        self.count_sarcasm = 0
        self.count_not = 0

        # bigrams
        self.bi_vocab = set()
        self.bigrams_sarcasm = defaultdict(int)
        self.bigrams_not = defaultdict(int)
        self.count_sarcasm_bigram = 0
        self.count_not_bigram = 0

    def buildSplit(self):
        split = self.tsplit()
        k = ['not','sarcasm']
        data = naive_headlines()
        d = list(data.keys())
        s = list(data.values())
        tt = TweetTokenizer()
        for i in range(len(data)):
            inst = self.instance()
            inst.words = tt.tokenize(d[i])
            inst.klass = k[int(s[i])]
            if random.random() < 0.7:
                split.train.append(inst)
            else:
                split.dev.append(inst)
        return split

    def classify(self, words):
        
        if(self.USE_BIGRAMS):
            words.insert(0,'<s>')
            words.append('</s>')

            pr_sarcasm = pr_not = 0
            if not self.sarcasm_docs == 0:
                pr_sarcasm += math.log(self.sarcasm_docs) - math.log(self.total_docs)
            if not self.not_docs == 0:
                pr_not = math.log(self.not_docs) - math.log(self.total_docs)

            sarcasm_denom = self.count_sarcasm_bigram + len(self.bi_vocab)
            not_denom = self.count_not_bigram + len(self.bi_vocab)

            for fword,sword in zip(words[:-1],words[1:]):
                if (fword,sword) in self.bi_vocab:
                    pr_sarcasm += math.log((self.bigrams_sarcasm[(fword,sword)] + 1)) - math.log(sarcasm_denom)
                    pr_not += math.log((self.bigrams_not[(fword,sword)] + 1)) - math.log(not_denom)

            if pr_sarcasm > pr_not:
                return 'sarcasm'
            return 'not'

        else:
            pr_sarcasm = pr_not = 0
            if not self.sarcasm_docs == 0:
                pr_sarcasm += math.log(self.sarcasm_docs) - math.log(self.total_docs)
            if not self.not_docs == 0:
                pr_not += math.log(self.not_docs) - math.log(self.total_docs)

            sarcasm_denom = self.count_sarcasm + len(self.vocab)
            not_denom = self.count_not + len(self.vocab)

            for word in words:
                if word in self.vocab:
                    pr_sarcasm += math.log((self.words_sarcasm[word] + 1)) - math.log(sarcasm_denom)
                    pr_not += math.log((self.words_not[word] + 1)) - math.log(not_denom)

            if pr_sarcasm > pr_not:
                return 'sarcasm'
            return 'not'

    def addExample(self, klass, words):
        """
         * TODO
         * Train your model on an example document with label klass ('sarcasm' or 'not') and
         * words, a list of strings.
         * You should store whatever data structures you use for your classifier 
         * in the NaiveBayes class.
         * Returns nothing
        """
        if klass == 'sarcasm':
            self.sarcasm_docs += 1
        else:
            self.not_docs += 1
        self.total_docs += 1

        if(self.USE_BIGRAMS):
            words.insert(0,'<s>')
            words.append('</s>')
            
            for fword,sword in zip(words[:-1],words[1:]):
                if klass == 'sarcasm':
                    self.count_sarcasm_bigram += 1
                    self.bigrams_sarcasm[(fword,sword)] += 1
                else:
                    self.count_not_bigram += 1
                    self.bigrams_not[(fword,sword)] += 1
                self.bi_vocab.add((fword,sword))

        else:
            for word in words:
                if klass == 'sarcasm':
                    self.count_sarcasm += 1
                    self.words_sarcasm[word] += 1
                else:
                    self.count_not += 1
                    self.words_not[word] += 1
                self.vocab.add(word)

def evaluate(USE_BIGRAMS):
    classifier = NaiveBayes()
    classifier.USE_BIGRAMS = USE_BIGRAMS
    split = classifier.buildSplit()
   
    for example in split.train:
        classifier.addExample(example.klass,example.words)

    train_accuracy = calculate_accuracy(split.train,classifier)
    dev_accuracy = calculate_accuracy(split.dev,classifier)

    print('Train Accuracy: {}'.format(train_accuracy))
    print('Dev Accuracy: {}'.format(dev_accuracy))

def calculate_accuracy(dataset,classifier):
    acc = 0.0
    if len(dataset) == 0:
        return 0.0
    else:
        for example in dataset:
            guess = classifier.classify(example.words)
            if example.klass == guess:
                acc += 1.0
        return acc / len(dataset)

def main():
    #evaluate(False)
    # data = naive_headlines()
    # X_train, X_test, y_train, y_test = train_test_split(list(data.keys()), list(data.values()), random_state=1)
    # print(X_test)
    # cv = CountVectorizer()
    # X_train_cv = cv.fit_transform(X_train)
    # X_test_cv = cv.transform(X_test)
    # nb = MultinomialNB()
    # nb.fit(X_train_cv, y_train)
    # predictions = nb.predict(X_train_cv)
    # print('Accuracy score: ', accuracy_score(y_train, predictions))
    # print('Precision score: ', precision_score(y_train, predictions))
    # print('Recall score: ', recall_score(y_train, predictions))

    # lr = LogisticRegression()
    # lr.max_iter = 10000
    # lr.fit(X_train_cv,y_train)
    # predictions = lr.predict(X_train_cv)
    # print('Accuracy score: ', accuracy_score(y_train, predictions))
    # print('Precision score: ', precision_score(y_train, predictions))
    # print('Recall score: ', recall_score(y_train, predictions))

    comments = read_reddit()
    labels = read_reddit_label()
    y_train = list(labels.values())
    X_train = [comments[i]['text'] for i in list(labels.keys())]
    labels = read_reddit_label('data/reddit/test-balanced.csv')
    cv = CountVectorizer()
    y_test = list(labels.values())
    X_test = [comments[i]['text'] for i in list(labels.keys())]
    X_train_cv = cv.fit_transform(X_train)
    X_test_cv = cv.transform(X_test)
    # nb = MultinomialNB()
    # nb.fit(X_train_cv, y_train)
    # predictions = nb.predict(X_test_cv)
    # print('Accuracy score: ', accuracy_score(y_test, predictions))
    # print('Precision score: ', precision_score(y_test, predictions))
    # print('Recall score: ', recall_score(y_test, predictions))

    lr = LogisticRegression()
    lr.fit(X_train_cv,y_train)
    predictions = lr.predict(X_test_cv)
    print('Accuracy score: ', accuracy_score(y_test, predictions))
    print('Precision score: ', precision_score(y_test, predictions))
    print('Recall score: ', recall_score(y_test, predictions))

    # Adaboost Classifier
    abc = AdaBoostClassifier(n_estimators=1000, learning_rate = 0.9, random_state=0)
    abc.fit(X_train_cv, y_train)
    predictions = abc.predict(X_test_cv)
    print('Adaboost Accuracy score: ', accuracy_score(y_test, predictions))
    print('Adaboost Precision score: ', precision_score(y_test, predictions))
    print('Adaboost Recall score: ', recall_score(y_test, predictions))

    # Random Forest - precision score is wonky, produces errors
    # rf = RandomForestClassifier(max_depth=2, random_state=0)
    # rf.fit(X_train_cv, y_train)
    # predictions = rf.predict(X_test_cv)
    # print('RandomForest Accuracy score: ', accuracy_score(y_test, predictions))
    # print('RandomForest Precision score: ', precision_score(y_test, predictions))
    # print('RandomForest Recall score: ', recall_score(y_test, predictions))

    # Gradient Boosting
    gb = GradientBoostingClassifier(loss='deviance')
    gb.fit(X_train_cv, y_train)
    predictions = gb.predict(X_test_cv)
    print('GB Accuracy score: ', accuracy_score(y_test, predictions))
    print('GB Precision score: ', precision_score(y_test, predictions))
    print('GB Recall score: ', recall_score(y_test, predictions))

    # K-neighbors
    # kn = KNeighborsClassifier()
    # kn.fit(X_train_cv2, y_train)
    # predictions = kn.predict(X_test_cv2)
    # print('KN Accuracy score: ', accuracy_score(y_test, predictions))
    # print('KN Precision score: ', precision_score(y_test, predictions))
    # print('KN Recall score: ', recall_score(y_test, predictions))

if __name__ == "__main__":
    main()