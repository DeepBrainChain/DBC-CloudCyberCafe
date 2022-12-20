import os

# 数组去重
def deduplication(lst, str = ''):
  ret = []
  for item in lst:
    if item != str:
      ret.append(item)
  return ret
