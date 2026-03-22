# Sample Data

This directory contains a small, manually curated sample of Colombian political posts for demo and testing purposes.

## sample_posts.json

Contains 25 sample posts representing the variety of Colombian political discourse:

- **Pro-Petro content**: Support for the current government and its policies
- **Anti-Petro content**: Opposition criticism and negative sentiment
- **Neutral news**: Factual reporting from major outlets
- **Electoral content**: Election-related discussion and campaign coverage
- **Colombian slang**: Posts using characteristic Colombian political slang
- **Social leaders**: Content about social leader killings and human rights
- **Manipulation signals**: Content about bodegas, trolls, and digital manipulation

Each post has: `id`, `text`, `source`, `platform`, `author`, `timestamp`, `url`

## Usage

```python
import json

with open("data/sample/sample_posts.json") as f:
    posts = json.load(f)
```
