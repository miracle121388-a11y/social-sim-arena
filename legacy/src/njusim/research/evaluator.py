"""Evaluator-owned synthetic labels. A production evaluator needs process/ACL isolation."""
class SyntheticOracle:
    def __init__(self, labels):
        if any(type(y) is not int or y not in (0,1) for y in labels.values()):
            raise ValueError("Synthetic oracle needs observed binary labels")
        self.__labels = dict(labels)

    def read_label(self, query_id):
        return self.__labels[query_id]
