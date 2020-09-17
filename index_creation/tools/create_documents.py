"""
Example script to create elasticsearch documents.
"""
import json
import time
import argparse

from tqdm import tqdm
import pandas as pd

from bert_serving.client import BertClient
bc = BertClient(output_fmt='list', check_version=False)


def create_document(doc, emb, index_name):
    return {
        '_op_type': 'index',
        '_index': index_name,
        'text': doc['text'],
        'title': doc['title'],
        'text_vector': emb
    }


def load_dataset(path):
    docs = []
    df = pd.read_csv(path, dtype=str)
    for row in tqdm(df.iterrows(), total=df.shape[0]):
        series = row[1]
        doc = {
            'title': series.Title,
            'text': series.Text
        }
        docs.append(doc)
    return docs


def bulk_predict(docs, batch_size=256):
    """Predict bert embeddings."""
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i: i+batch_size]
        embeddings = bc.encode([str(doc['text']) for doc in batch_docs])
        for emb in embeddings:
            yield emb


def main(args):
    print("Loading dataset...")
    docs = load_dataset(args.data)
    with open(args.save, 'w+') as f:
        print("Encoding dataset...")
        for doc, emb in tqdm(zip(docs, bulk_predict(docs)), total=len(docs)):
            d = create_document(doc, emb, args.index_name)
            f.write(json.dumps(d) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creating elasticsearch documents.')
    parser.add_argument('--data', help='data for creating documents.')
    parser.add_argument('--save', help='created documents.')
    parser.add_argument('--index_name', default='rfcsearch', help='Elasticsearch index name.')
    args = parser.parse_args()
    main(args)
