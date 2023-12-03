# -*- coding: utf-8 -*-
"""recomdsystm.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19wiRGgtlhoREAm5hgz8x6Jw9LANNLcWH
"""

import pandas as pd
import numpy as np
import os
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import mean_squared_error
from random import randint
import json

def find_avr(x):
  s = 0
  num = 0
  for el in x:
    if (el != 0):
      s += el
      num += 1
  if (num == 0): return 0
  return s / num

def count_sim(x, y):
  if (len(x) != len(y)): return None
  x_mean = find_avr(x)
  y_mean = find_avr(y)

  sum_xy = 0
  sum_x2 = 0
  sum_y2 = 0
  for i in range(len(x)):
    if x[i] == 0: xi = x[i]
    else: xi = x[i] - x_mean
    if y[i] == 0: yi = y[i]
    else: yi = y[i] - y_mean
    sum_xy += xi*yi
    sum_x2 += xi**2
    sum_y2 += yi**2
  if (sum_x2**0.5 * sum_y2**0.5 == 0): return None
  rez = sum_xy / (sum_x2**0.5 * sum_y2**0.5)
  return rez

def transform_user(users):
  user_enc = LabelEncoder()
  users['occupation_enc'] = user_enc.fit_transform(users['occupation'].values)
  zip_enc = LabelEncoder()
  users['zip_code'] = zip_enc.fit_transform(users['zip_code'].values)
  users = users.drop(['occupation'], axis=1)

  user_vectors = []
  for i in range(len(users)):
    user_vectors.append([users['age'][i], users['gender'][i],
                        users['zip_code'][i], users['occupation_enc'][i]])
  users['u_vector'] = user_vectors
  return users

def transform_item(items):
  item_enc = LabelEncoder()
  items['title_enc'] = item_enc.fit_transform(items['title'].values)
  rel_enc = LabelEncoder()
  items['release_enc'] = rel_enc.fit_transform(items['release'].values)
  items = items.drop(['release'], axis=1)
  return items, item_enc

def create_coll_filt(data, users, items_size):
  coll_filt = np.zeros((items_size,len(users)))
  for row in range(len(data)):
    item = data['item_id'][row]
    user = data['user_id'][row]
    coll_filt[item-1][user-1] = data['rating'][row]

  user_user_sim = np.zeros((len(users),len(users)))
  for u1 in range(len(users)):
    for u2 in range(u1, len(users)):
      Sij = count_sim(users['u_vector'][u1], users['u_vector'][u2])
      user_user_sim[u1][u2] = Sij
      if (u1 != u2): user_user_sim[u2][u1] = Sij
  return coll_filt, user_user_sim

def train_tree_set(data, items, users_size):
  full_data = pd.merge(data, items)

  datasets = dict()
  for user in range(1, users_size+1):
    df = pd.DataFrame(columns=['unknown','Action', 'Adventure','Animation',
                              "Children's", 'Comedy', 'Crime','Documentary',
                              'Drama','Fantasy','Film-Noir','Horror', 'Musical',
                              'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War',
                              'Western','title_enc', 'release_enc', 'rating'])
    datasets[user] = df
  for row in range(len(full_data)):
    user = full_data['user_id'][row]
    new_row = []
    for col in full_data.columns[5:]:
      new_row.append(full_data[col][row])
    new_row.append(full_data['rating'][row])
    datasets[user].loc[len(datasets[user])] = new_row

  tree_set = dict()
  for user in range(1, users_size+1):
    clf_tree = DecisionTreeClassifier(criterion = 'entropy', random_state = 100,
                                      max_depth = 3, min_samples_leaf = 5)
    tree_set[user] = clf_tree
    X_train = datasets[user].drop(['rating'], axis=1)
    y_train = datasets[user]['rating'].values
    tree_set[user].fit(X_train, y_train)
  return tree_set, full_data

### Class with model

class Recomendation_System:
  def __init__(self, data_, user_, item_):
    self.data = data_
    self.users = transform_user(user_)
    self.items, self.title_enc = transform_item(item_)

    self.coll_filt, self.user_user_sim = create_coll_filt(self.data, self.users, len(self.items))
    self.tree_set, self.full_data = train_tree_set(self.data, self.items, len(self.users))

  def predict_rating_UtoU(self, user, item):
    sim_list = list()
    for i in range(len(self.users)):
      if (user-1 == i): continue
      sim = self.user_user_sim[user-1][i]
      if (sim < 0): continue
      if (self.coll_filt[item-1][i] == 0): continue
      sim_list.append((sim, i))
    pred_rating = 0
    num = 0
    for (sim, indx) in sim_list:
      pred_rating += self.coll_filt[item-1][indx] * sim
      num += sim
    if (num == 0): return 0.0
    pred_rating = pred_rating / num
    return pred_rating

  def predict_raiting_tree(self, user, item):
    df = pd.DataFrame(columns=['unknown','Action', 'Adventure','Animation',
                             "Children's", 'Comedy', 'Crime','Documentary',
                             'Drama','Fantasy','Film-Noir','Horror', 'Musical',
                             'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War',
                             'Western','title_enc', 'release_enc'])
    new_row = []
    for col in self.full_data.columns[5:26]:
      new_row.append(self.full_data[col][0])
    df.loc[0] = new_row
    pred_rating = self.tree_set[196].predict(df)
    return pred_rating[0]

  def get_ratings_CF(self, user, possible_items):
    ratings = list()
    for item in possible_items:
      pred_r = self.predict_rating_UtoU(user, item)
      if (pred_r != 0):
        ratings.append((round(pred_r-0.5), item))
    return ratings

  def get_ratings_CB(self, user, possible_items):
    ratings = list()
    for item in possible_items:
      pred_r = self.predict_raiting_tree(user, item)
      ratings.append((round(pred_r+0.8), item))
    return ratings

  def recommend_for_user(self, user, top=10, method='hybrid', with_predictions=False):
    all_itms = set([i for i in range(1, len(self.items)+1)])
    for row in range(len(self.data)):
      item_ = self.data['item_id'][row]
      user_ = self.data['user_id'][row]
      if (user_ != user): continue
      all_itms.remove(item_)
    possible_items = list(all_itms)

    ratings = list()
    if (method == 'coll_filtr'):
      ratings = self.get_ratings_CF(user, possible_items)
    elif (method == 'content_b'):
      ratings = self.get_ratings_CB(user, possible_items)
    elif (method == 'hybrid'):
      ratingCF = self.get_ratings_CF(user, possible_items)
      dictCF = dict()
      for (r, item) in ratingCF:
        dictCF[item] = r
      ratings = self.get_ratings_CB(user, possible_items)
      for i in range(len(ratings)):
        if (ratings[i][1] in dictCF):
          if (randint(1,2) % 2 == 0):
            ratings[i] = (dictCF[ratings[i][1]], ratings[i][1])
          dictCF.pop(ratings[i][1])
      for item in list(dictCF.keys()):
        ratings.append((dictCF[item], item))
    else:
      print("Error: only 'content_b'/'coll_filtr'/'hybrid' method")
      return None

    ratings.sort()
    ratings.reverse()
    result = []
    for (rating, item_id) in ratings:
      if (with_predictions):
        result.append((self.items['title'][item_id - 1], rating))
      else:
        result.append(self.items['title'][item_id - 1])
      if (len(result) == top): break
    return result