import os

# 数组去重
def deduplication(lst, str = ''):
  ret = []
  for item in lst:
    if item != str:
      ret.append(item)
  return ret

# 除了 index 行，不与数组 lst 的其他行的值相同
def isin(value, lst, index):
  if index is None or index > len(lst):
    return lst.count(value) > 0
  lst.pop(index)
  return lst.count(value) > 0
