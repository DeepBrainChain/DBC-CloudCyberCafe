#include "cross_util.h"

#include <algorithm>

namespace {
 bool isntspace(const char& ch) {
         return !isspace(ch);
 }
 } // end of namespace
 
std::string ltrim(const std::string& s, char ch) {
  std::string::const_iterator iter = std::find_if(s.begin(), s.end(),
    [&ch](char c) { return ch != c;});
  return std::string(iter, s.end());
 }
 
std::string rtrim(const std::string& s, char ch) {
  std::string::const_iterator iter = std::find_if(s.rbegin(), s.rend(),
    [&ch](char c) { return ch != c;}).base();
  return std::string(s.begin(), iter);
 }
 
std::string trim(const std::string& s, char ch) {
  std::string::const_iterator iter1 = std::find_if(s.begin(), s.end(),
    [&ch](char c) { return ch != c;});
  std::string::const_iterator iter2 = std::find_if(s.rbegin(), s.rend(),
    [&ch](char c) { return ch != c;}).base();

  return iter1 < iter2 ? std::string(iter1, iter2) : std::string("");
 }
