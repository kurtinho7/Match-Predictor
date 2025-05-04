import sklearn
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score

def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols] \
        .rolling(3, closed='left') \
        .mean() \
        .rename(columns=dict(zip(cols, new_cols)))
    group = group.join(rolling_stats)
    return group.dropna(subset=new_cols)


def make_predictions(data, predictors):
    train = data[data["date"] < '2025-02-02']
    test = data[data["date"] >= '2025-02-02']
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    error = precision_score(test["target"], preds)
    accuracy = accuracy_score(test["target"], preds)
    return combined, error, accuracy

cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt", "xg", "xga", "poss", "sca", "passlive", "passdead", "to", "fld", "def"]
new_cols = [f"{c}_rolling" for c in cols]


matches = pd.read_csv("matches.csv", index_col= 0)
matches["date"] = pd.to_datetime(matches["date"])
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype(int)
matches["day_code"] = matches["date"].dt.dayofweek
matches["target"] = (matches["result"] == "W").astype(int)

predictors = ["venue_code", "opp_code", "hour", "day_code"]

rf = RandomForestClassifier(n_estimators=50, min_samples_split=20, random_state=1)

matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))
matches_rolling = matches_rolling.droplevel('team')

matches_rolling.index = range(matches_rolling.shape[0])

combined, error, accuracy = make_predictions(matches_rolling, predictors + new_cols)

print(error)
print(accuracy)

combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values = {"Brighton and Hove Albion": "Brighton", "Manchester United": "Manchester Utd", "Newcastle United": "Newcastle Utd", "Tottenham Hotspur": "Tottenham", "West Ham United": "West Ham", "Wolverhampton Wanderers": "Wolves", "Nottingham Forest": "Nott'ham Forest"} 
mapping = MissingDict(**map_values)


combined["new_team"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date", "new_team"], right_on=["date", "opponent"])

print(merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] ==0)]["actual_x"].value_counts())



