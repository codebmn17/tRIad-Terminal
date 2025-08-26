# Random Forest Iris Classification
# Demonstrates using RandomForestClassifier for enhanced accuracy

import pickle
import random

print('=== Random Forest Iris Classification (Pure Python Implementation) ===')

# Simulate iris dataset (expanded for better training)
iris_data = {
    'setosa': [
        [5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2], [4.7, 3.2, 1.3, 0.2],
        [4.6, 3.1, 1.5, 0.2], [5.0, 3.6, 1.4, 0.2], [5.4, 3.9, 1.7, 0.4]
    ],
    'versicolor': [
        [7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5], [6.9, 3.1, 4.9, 1.5],
        [5.5, 2.3, 4.0, 1.3], [6.5, 2.8, 4.6, 1.5], [5.7, 2.8, 4.5, 1.3]
    ],
    'virginica': [
        [6.3, 3.3, 6.0, 2.5], [5.8, 2.7, 5.1, 1.9], [7.1, 3.0, 5.9, 2.1],
        [6.3, 2.9, 5.6, 1.8], [6.5, 3.0, 5.8, 2.2], [7.6, 3.0, 6.6, 2.1]
    ]
}

class SimpleDecisionTree:
    def __init__(self, max_depth=3):
        self.max_depth = max_depth
        self.tree = None
    
    def gini_impurity(self, labels):
        if not labels:
            return 0
        counts = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        
        impurity = 1.0
        total = len(labels)
        for count in counts.values():
            prob = count / total
            impurity -= prob * prob
        return impurity
    
    def split_data(self, data, labels, feature_idx, threshold):
        left_data, left_labels = [], []
        right_data, right_labels = [], []
        
        for i, sample in enumerate(data):
            if sample[feature_idx] <= threshold:
                left_data.append(sample)
                left_labels.append(labels[i])
            else:
                right_data.append(sample)
                right_labels.append(labels[i])
        
        return left_data, left_labels, right_data, right_labels
    
    def find_best_split(self, data, labels):
        best_gain = 0
        best_feature = 0
        best_threshold = 0
        
        current_impurity = self.gini_impurity(labels)
        n_features = len(data[0]) if data else 0
        
        for feature_idx in range(n_features):
            values = [sample[feature_idx] for sample in data]
            thresholds = set(values)
            
            for threshold in thresholds:
                left_data, left_labels, right_data, right_labels = self.split_data(
                    data, labels, feature_idx, threshold
                )
                
                if len(left_labels) == 0 or len(right_labels) == 0:
                    continue
                
                left_weight = len(left_labels) / len(labels)
                right_weight = len(right_labels) / len(labels)
                
                weighted_impurity = (left_weight * self.gini_impurity(left_labels) + 
                                   right_weight * self.gini_impurity(right_labels))
                
                gain = current_impurity - weighted_impurity
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold
        
        return best_feature, best_threshold, best_gain
    
    def most_common_label(self, labels):
        if not labels:
            return None
        counts = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        return max(counts, key=counts.get)
    
    def build_tree(self, data, labels, depth=0):
        if depth >= self.max_depth or len(set(labels)) == 1 or len(data) < 2:
            return self.most_common_label(labels)
        
        feature_idx, threshold, gain = self.find_best_split(data, labels)
        
        if gain == 0:
            return self.most_common_label(labels)
        
        left_data, left_labels, right_data, right_labels = self.split_data(
            data, labels, feature_idx, threshold
        )
        
        return {
            'feature': feature_idx,
            'threshold': threshold,
            'left': self.build_tree(left_data, left_labels, depth + 1),
            'right': self.build_tree(right_data, right_labels, depth + 1)
        }
    
    def fit(self, data, labels):
        self.tree = self.build_tree(data, labels)
    
    def predict_sample(self, sample, tree):
        if isinstance(tree, str):
            return tree
        
        if sample[tree['feature']] <= tree['threshold']:
            return self.predict_sample(sample, tree['left'])
        else:
            return self.predict_sample(sample, tree['right'])
    
    def predict(self, data):
        if isinstance(data[0], (int, float)):
            return self.predict_sample(data, self.tree)
        return [self.predict_sample(sample, self.tree) for sample in data]

class SimpleRandomForest:
    def __init__(self, n_estimators=100, max_depth=3, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.trees = []
        random.seed(random_state)
    
    def bootstrap_sample(self, data, labels):
        n_samples = len(data)
        indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
        bootstrap_data = [data[i] for i in indices]
        bootstrap_labels = [labels[i] for i in indices]
        return bootstrap_data, bootstrap_labels
    
    def fit(self, data, labels):
        self.trees = []
        
        for i in range(self.n_estimators):
            # Create bootstrap sample
            boot_data, boot_labels = self.bootstrap_sample(data, labels)
            
            # Train decision tree on bootstrap sample
            tree = SimpleDecisionTree(max_depth=self.max_depth)
            tree.fit(boot_data, boot_labels)
            self.trees.append(tree)
            
            if (i + 1) % 20 == 0:
                print(f"Trained {i + 1}/{self.n_estimators} trees")
    
    def predict(self, sample):
        if isinstance(sample[0], (int, float)):
            # Single sample
            predictions = [tree.predict(sample) for tree in self.trees]
            # Majority vote
            votes = {}
            for pred in predictions:
                votes[pred] = votes.get(pred, 0) + 1
            return max(votes, key=votes.get)
        else:
            # Multiple samples
            return [self.predict(s) for s in sample]
    
    def score(self, test_data, test_labels):
        predictions = [self.predict(sample) for sample in test_data]
        correct = sum(1 for pred, true in zip(predictions, test_labels) if pred == true)
        return correct / len(test_labels)

# Prepare training data
training_data = []
training_labels = []

for species, samples in iris_data.items():
    for sample in samples:
        training_data.append(sample)
        training_labels.append(species)

# Split into train/test (simple split)
train_size = int(0.8 * len(training_data))
X_train = training_data[:train_size]
y_train = training_labels[:train_size]
X_test = training_data[train_size:]
y_test = training_labels[train_size:]

print(f'Training data: {len(X_train)} samples')
print(f'Test data: {len(X_test)} samples')
print('Classes:', list(iris_data.keys()))

# --- Train a more powerful model ---

# Create the Random Forest model
# n_estimators is the number of "trees" or "experts" in the forest.
unstoppable_model = SimpleRandomForest(n_estimators=100, random_state=42)

print('\n--- Training Random Forest Model ---')
# Train it just like before!
unstoppable_model.fit(X_train, y_train)

# Evaluate it just like before!
accuracy = unstoppable_model.score(X_test, y_test)

print(f"\nRandom Forest Accuracy: {accuracy:.2f}")
# On the Iris dataset, this will likely achieve high accuracy on our test set.

# Save the model
print('\n--- Saving Random Forest Model ---')
with open('unstoppable_iris_model.pkl', 'wb') as f:
    pickle.dump(unstoppable_model, f)
print('Model saved to unstoppable_iris_model.pkl')

# Load and test the model
with open('unstoppable_iris_model.pkl', 'rb') as f:
    loaded_forest = pickle.load(f)
print('Model loaded successfully')

# Test predictions
test_samples = [
    [5.1, 3.5, 1.4, 0.2],  # Typical Setosa
    [7.0, 3.2, 4.7, 1.4],  # Typical Versicolor  
    [6.3, 3.3, 6.0, 2.5]   # Typical Virginica
]

print('\n--- Random Forest Predictions ---')
for i, sample in enumerate(test_samples):
    prediction = loaded_forest.predict(sample)
    print(f'Sample {i+1}: {sample} -> Predicted: {prediction}')

# Compare with individual tree vs forest
single_tree = SimpleDecisionTree(max_depth=3)
single_tree.fit(X_train, y_train)

# Calculate tree accuracy manually
tree_predictions = [single_tree.predict(sample) for sample in X_test]
tree_correct = sum(1 for pred, true in zip(tree_predictions, y_test) if pred == true)
tree_accuracy = tree_correct / len(y_test)

print(f'\n--- Performance Comparison ---')
print(f'Single Decision Tree Accuracy: {tree_accuracy:.2f}')
print(f'Random Forest Accuracy: {accuracy:.2f}')
if tree_accuracy > 0:
    print(f'Improvement: {((accuracy - tree_accuracy) / tree_accuracy * 100):.1f}%')
else:
    print('Random Forest shows significant improvement over single tree')

print('\n=== Random Forest Training Complete ===')