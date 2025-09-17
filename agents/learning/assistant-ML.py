#!/usr/bin/env python3
"""
Backward compatibility shim for assistant-ML.py
"""

import json
import logging
import os
import pickle
import re
import threading
import time
from datetime import datetime
from typing import Any
import numpy as np

# Optional ML dependencies with graceful fallbacks
try:
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# For deeper learning models
try:
    import tensorflow as tf
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Embedding
    from tensorflow.keras.models import Sequential, load_model, save_model
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.preprocessing.text import Tokenizer

    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

logger = logging.getLogger("triad.ai")


def log_with_context(level: str, message: str, component: str, event: str, **kwargs) -> None:
    """
    def log_with_context(level: str, message: str, component: str, event: str, **kwargs) -> None:
    """
    Structured logging helper with context information.

 copilot/fix-c1e50cd2-35ad-4991-8bc0-a59778375133

    Args:
        level: log level
        message: log message
        component: component name
        event: event name
        kwargs: extra data
    """
    # TODO: implement
    """
    Structured logging helper with context information.

    Args:
        level: ...
        message: ...
        ...
    """
    # function body...
    
 main
    Args:
        level: Log level (info, warning, error, debug)
        message: Log message
        component: Component name (e.g., 'predictor', 'nl_processor', 'code_engine')
        event: Event type (e.g., 'prediction', 'training', 'initialization')
        **kwargs: Additional context data
    """
    context = {"component": component, "event": event, **kwargs}

    log_message = f"[{component}:{event}] {message}"
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        if context_str:
            log_message += f" | {context_str}"

    getattr(logger, level.lower())(log_message)


class CodeCompletionEngine:
    """Engine for providing code completions"""

    def __init__(self, model_dir: str = "~/.triad/ai/models"):
        self.model_dir = os.path.expanduser(model_dir)
        os.makedirs(self.model_dir, exist_ok=True)

        self.language_models = {}
        self.tokenizers = {}
        self.vectorizers = {}

        # Initialize model trackers
        self.supported_languages = ["python", "javascript", "bash", "sql"]
        self.ready = False

        # Training data
        self.code_samples = {lang: [] for lang in self.supported_languages}
        self.max_samples = 1000  # Max samples per language

        # Load existing models
        self._load_models()

    def _load_models(self) -> None:
        """Load trained models if available"""
        if not HAS_SKLEARN:
            log_with_context(
                "warning",
                "scikit-learn not available, code completion will be limited",
                "code_engine",
                "initialization",
            )
            return

        for language in self.supported_languages:
            # Load vectorizer
            vectorizer_path = os.path.join(self.model_dir, f"{language}_vectorizer.pkl")
            if os.path.exists(vectorizer_path):
                try:
                    self.vectorizers[language] = joblib.load(vectorizer_path)
                    log_with_context(
                        "info",
                        f"Loaded vectorizer for {language}",
                        "code_engine",
                        "initialization",
                        language=language,
                    )
                except Exception as e:
                    log_with_context(
                        "error",
                        f"Failed to load vectorizer for {language}",
                        "code_engine",
                        "initialization",
                        language=language,
                        error=str(e),
                    )

            # Load simple completion model
            model_path = os.path.join(self.model_dir, f"{language}_completion_model.pkl")
            if os.path.exists(model_path):
                try:
                    self.language_models[language] = joblib.load(model_path)
                    logger.info(f"Loaded completion model for {language}")
                except Exception as e:
                    logger.error(f"Failed to load model for {language}: {e}")

        # Load neural models if TensorFlow is available
        if HAS_TENSORFLOW:
            for language in self.supported_languages:
                tokenizer_path = os.path.join(self.model_dir, f"{language}_tokenizer.pkl")
                if os.path.exists(tokenizer_path):
                    try:
                        with open(tokenizer_path, "rb") as f:
                            self.tokenizers[language] = pickle.load(f)
                        logger.info(f"Loaded tokenizer for {language}")
                    except Exception as e:
                        logger.error(f"Failed to load tokenizer for {language}: {e}")

                nn_model_path = os.path.join(self.model_dir, f"{language}_nn_model")
                if os.path.exists(nn_model_path):
                    try:
                        # Load the neural model
                        model = load_model(nn_model_path)
                        self.language_models[f"{language}_nn"] = model
                        logger.info(f"Loaded neural model for {language}")
                    except Exception as e:
                        logger.error(f"Failed to load neural model for {language}: {e}")

        # Set ready status
        self.ready = any(self.language_models)

        if self.ready:
            logger.info("Code completion engine initialized with pre-trained models")
        else:
            logger.info("Code completion engine initialized, no pre-trained models found")

    def add_code_sample(self, code: str, language: str) -> bool:
        """Add a code sample for training"""
        if language not in self.supported_languages:
            return False

        # Add to samples if not at limit
        if len(self.code_samples[language]) < self.max_samples:
            self.code_samples[language].append(code)
            return True

        # If at limit, replace a random sample
        import random

        idx = random.randint(0, self.max_samples - 1)
        self.code_samples[language][idx] = code
        return True

    def train_models(self, background: bool = True) -> bool:
        """Train the completion models using collected code samples"""
        if not HAS_SKLEARN:
            logger.warning("scikit-learn not available, cannot train models")
            return False

        # Check if we have enough data
        has_data = False
        for lang, samples in self.code_samples.items():
            if len(samples) >= 10:  # Minimum samples to train
                has_data = True
                break

        if not has_data:
            logger.warning("Not enough code samples to train models")
            return False

        # Train in background thread if requested
        if background:
            thread = threading.Thread(target=self._train_models_task)
            thread.daemon = True
            thread.start()
            return True
        else:
            return self._train_models_task()

    def _train_models_task(self) -> bool:
        """Internal training task"""
        try:
            logger.info("Starting model training...")

            for language, samples in self.code_samples.items():
                if len(samples) < 10:
                    logger.info(f"Skipping {language} training, not enough samples")
                    continue

                logger.info(f"Training {language} model with {len(samples)} samples")

                # Prepare training data
                token_sequences = []
                next_tokens = []

                # Split code into token sequences
                for code in samples:
                    tokens = self._tokenize_code(code, language)
                    for i in range(3, len(tokens)):
                        token_sequences.append(" ".join(tokens[i - 3 : i]))
                        next_tokens.append(tokens[i])

                if len(token_sequences) < 10:
                    logger.info(f"Not enough token sequences for {language}")
                    continue

                # Create and train TF-IDF vectorizer
                vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 3), max_features=5000)
                X = vectorizer.fit_transform(token_sequences)
                y = next_tokens

                # Train a simple model
                model = KNeighborsClassifier(n_neighbors=5)
                model.fit(X, y)

                # Save the trained model and vectorizer
                self.vectorizers[language] = vectorizer
                self.language_models[language] = model

                joblib.dump(vectorizer, os.path.join(self.model_dir, f"{language}_vectorizer.pkl"))
                joblib.dump(model, os.path.join(self.model_dir, f"{language}_completion_model.pkl"))

                logger.info(f"Completed training {language} model")

                # Train neural model if TensorFlow is available
                if HAS_TENSORFLOW and len(samples) >= 50:
                    try:
                        self._train_neural_model(language, samples)
                    except Exception as e:
                        logger.error(f"Failed to train neural model for {language}: {e}")

            self.ready = True
            logger.info("Model training completed")
            return True

        except Exception as e:
            logger.error(f"Error during model training: {e}")
            return False

    def _train_neural_model(self, language: str, samples: list[str]) -> None:
        """Train a neural model for more complex completions"""
        if not HAS_TENSORFLOW:
            return

        logger.info(f"Training neural model for {language}")

        # Prepare data
        all_text = "\n".join(samples)

        # Create or update tokenizer
        if language in self.tokenizers:
            tokenizer = self.tokenizers[language]
        else:
            tokenizer = Tokenizer()
            tokenizer.fit_on_texts([all_text])
            self.tokenizers[language] = tokenizer

        total_words = len(tokenizer.word_index) + 1

        # Create sequences for training
        input_sequences = []
        for sample in samples:
            token_list = tokenizer.texts_to_sequences([sample])[0]
            for i in range(1, len(token_list)):
                n_gram_sequence = token_list[: i + 1]
                input_sequences.append(n_gram_sequence)

        if len(input_sequences) < 10:
            logger.warning(f"Not enough sequences for neural training for {language}")
            return

        # Pad sequences
        max_sequence_len = max([len(x) for x in input_sequences])
        input_sequences = pad_sequences(input_sequences, maxlen=max_sequence_len, padding="pre")

        # Create training data
        X = input_sequences[:, :-1]
        y = input_sequences[:, -1]

        # Convert y to one-hot encoding
        y = tf.keras.utils.to_categorical(y, num_classes=total_words)

        # Create and train model
        model = Sequential()
        model.add(Embedding(total_words, 100, input_length=max_sequence_len - 1))
        model.add(LSTM(150, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(100))
        model.add(Dense(total_words, activation="softmax"))
        model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
        model.fit(X, y, epochs=30, verbose=0)

        # Save model and tokenizer
        model_path = os.path.join(self.model_dir, f"{language}_nn_model")
        save_model(model, model_path)

        tokenizer_path = os.path.join(self.model_dir, f"{language}_tokenizer.pkl")
        with open(tokenizer_path, "wb") as f:
            pickle.dump(tokenizer, f)

        # Add to models
        self.language_models[f"{language}_nn"] = model

        logger.info(f"Neural model for {language} trained and saved")

    def get_completion(
        self, code_context: str, language: str, max_suggestions: int = 3
    ) -> list[str]:
        """Get code completion suggestions based on context"""
        if not self.ready or language not in self.supported_languages:
            # Return static suggestions if models aren't ready
            return self._get_static_suggestions(code_context, language)

        # Basic suggestions using ML model
        suggestions = []

        try:
            # Try the neural model first if available
            if (
                HAS_TENSORFLOW
                and f"{language}_nn" in self.language_models
                and language in self.tokenizers
            ):
                nn_suggestions = self._get_neural_suggestions(code_context, language)
                if nn_suggestions:
                    suggestions.extend(nn_suggestions)

            # Use the simpler model if needed
            if language in self.language_models and language in self.vectorizers:
                simple_suggestions = self._get_simple_suggestions(code_context, language)
                if simple_suggestions:
                    # Add without duplicates
                    for sugg in simple_suggestions:
                        if sugg not in suggestions:
                            suggestions.append(sugg)

            # If we have suggestions, return them
            if suggestions:
                return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Error getting completion: {e}")

        # Fall back to static suggestions
        return self._get_static_suggestions(code_context, language)

    def _get_simple_suggestions(self, code_context: str, language: str) -> list[str]:
        """Get suggestions using the simple ML model"""
        # Get the most recent tokens
        tokens = self._tokenize_code(code_context, language)
        if len(tokens) < 3:
            return []

        # Create the context sequence
        context = " ".join(tokens[-3:])

        # Vectorize the context
        vectorizer = self.vectorizers[language]
        model = self.language_models[language]

        context_vector = vectorizer.transform([context])

        # Get nearest neighbors
        distances, indices = model.kneighbors(context_vector, n_neighbors=5)

        # Get the predicted next tokens
        next_tokens = [model.predict(context_vector)[0]]
        for i in indices[0]:
            y_pred = model._y[i]
            if y_pred not in next_tokens:
                next_tokens.append(y_pred)

        return next_tokens

    def _get_neural_suggestions(self, code_context: str, language: str) -> list[str]:
        """Get suggestions using the neural model"""
        if not HAS_TENSORFLOW:
            return []

        model = self.language_models[f"{language}_nn"]
        tokenizer = self.tokenizers[language]

        # Convert context to sequence
        token_list = tokenizer.texts_to_sequences([code_context])[0]
        if not token_list:
            return []

        # Limit context length to what the model expects
        input_shape = model.input_shape
        expected_length = input_shape[1] if len(input_shape) > 1 else 10
        token_list = token_list[-expected_length:]

        # Pad sequence
        token_list = pad_sequences([token_list], maxlen=expected_length, padding="pre")

        # Predict next token
        predicted = model.predict(token_list, verbose=0)

        # Get top 3 predictions
        predicted = predicted[0]
        top_indices = np.argsort(predicted)[-5:][::-1]

        # Convert back to words
        index_word = {v: k for k, v in tokenizer.word_index.items()}

        suggestions = []
        for idx in top_indices:
            if idx in index_word:
                suggestions.append(index_word[idx])

        return suggestions

    def _get_static_suggestions(self, code_context: str, language: str) -> list[str]:
        """Get static code suggestions based on language and context"""
        # Simplified language-specific suggestions
        context_lower = code_context.lower()

        if language == "python":
            if "def " in context_lower:
                return ["self", "return", "None"]
            elif "import" in context_lower:
                return ["os", "sys", "numpy", "pandas"]
            elif "if " in context_lower:
                return ["True:", "False:", "is None:"]
            elif "for " in context_lower:
                return ["in range(", "in ", "item in items:"]
            else:
                return ["def", "class", "import", "return"]

        elif language == "javascript":
            if "function" in context_lower:
                return ["() {", "(params) {", "=> {"]
            elif "const " in context_lower or "let " in context_lower:
                return ["= ", "= [", "= {"]
            elif "if " in context_lower:
                return ["(", "(condition) {", "=== "]
            else:
                return ["const", "function", "return", "=>"]

        elif language == "bash":
            if "if " in context_lower:
                return ["[ ", "[[ ", "-f ", "-d "]
            elif "for " in context_lower:
                return ["in ", "i in {1..10}", "file in *.txt"]
            else:
                return ["if", "for", "while", "echo"]

        elif language == "sql":
            if "select " in context_lower:
                return ["* from", "count(*) from", "distinct"]
            elif "where " in context_lower:
                return ["id = ", "name = '", "date >"]
            else:
                return ["SELECT", "INSERT INTO", "UPDATE", "DELETE FROM"]

        # Generic suggestions
        return ["()", "{}", "[]", "="]

    def _tokenize_code(self, code: str, language: str) -> list[str]:
        """Tokenize code based on language"""
        # Simple tokenization for different languages
        if language == "python" or language == "bash":
            # Split by whitespace, but keep important symbols
            tokens = re.findall(r"\b\w+\b|[^\w\s]", code)
        elif language == "javascript":
            # JS has more complex tokens
            tokens = re.findall(r"\b\w+\b|[^\w\s]|[=(){}\[\]]", code)
        elif language == "sql":
            # SQL is case-insensitive, so lowercase it
            tokens = re.findall(r"\b\w+\b|[^\w\s]", code.lower())
        else:
            # Generic tokenization
            tokens = re.findall(r"\b\w+\b|[^\w\s]", code)

        return tokens


class CommandPredictor:
    """Predicts commands based on history and context"""

    def __init__(self, history_file: str = "~/.triad/history/commands.json"):
        self.history_file = os.path.expanduser(history_file)
        self.history_dir = os.path.dirname(self.history_file)
        os.makedirs(self.history_dir, exist_ok=True)

        # Command history data
        self.commands = []
        self.command_frequencies = {}  # How often a command is used
        self.command_sequences = {}  # What commands follow others
        self.command_contexts = {}  # In what contexts commands are used

        # Load command history
        self._load_history()

        # Model for command prediction
        self.model = None
        self.vectorizer = None
        if HAS_SKLEARN:
            self._initialize_model()

    def _load_history(self) -> None:
        """Load command history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file) as f:
                    data = json.load(f)

                self.commands = data.get("commands", [])
                self.command_frequencies = data.get("frequencies", {})
                self.command_sequences = data.get("sequences", {})
                self.command_contexts = data.get("contexts", {})

                log_with_context(
                    "info",
                    f"Loaded {len(self.commands)} commands from history",
                    "predictor",
                    "initialization",
                    commands_count=len(self.commands),
                )

            except Exception as e:
                log_with_context(
                    "error",
                    "Error loading command history",
                    "predictor",
                    "initialization",
                    error=str(e),
                )
                self._initialize_empty_history()
        else:
            self._initialize_empty_history()

    def _initialize_empty_history(self) -> None:
        """Initialize empty command history"""
        self.commands = []
        self.command_frequencies = {}
        self.command_sequences = {}
        self.command_contexts = {}

    def _save_history(self) -> None:
        """Save command history to file"""
        try:
            data = {
                "commands": self.commands[-1000:],  # Keep last 1000 commands
                "frequencies": self.command_frequencies,
                "sequences": self.command_sequences,
                "contexts": self.command_contexts,
            }

            with open(self.history_file, "w") as f:
                json.dump(data, f)

            logger.debug("Command history saved")

        except Exception as e:
            logger.error(f"Error saving command history: {e}")

    def _initialize_model(self) -> None:
        """Initialize machine learning model for prediction"""
        if not HAS_SKLEARN or len(self.commands) < 10:
            return

        try:
            # Create vectorizer and training data
            self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5))

            # Extract unique commands
            unique_commands = list(set(self.commands))
            if len(unique_commands) < 2:
                return

            # Create features and labels
            X = self.vectorizer.fit_transform(unique_commands)

            # For each command, create a feature and a label (the command itself)
            y = unique_commands

            # Train a simple classifier
            self.model = LogisticRegression(max_iter=1000)
            self.model.fit(X, y)

            logger.info("Command prediction model initialized")

        except Exception as e:
            logger.error(f"Error initializing command prediction model: {e}")

    def add_command(self, command: str, context: str = None) -> None:
        """Add a command to history"""
        if not command or command.isspace():
            return

        # Add to commands list
        self.commands.append(command)

        # Update frequency
        self.command_frequencies[command] = self.command_frequencies.get(command, 0) + 1

        # Update sequence information
        if len(self.commands) >= 2:
            prev_cmd = self.commands[-2]
            if prev_cmd not in self.command_sequences:
                self.command_sequences[prev_cmd] = {}

            self.command_sequences[prev_cmd][command] = (
                self.command_sequences[prev_cmd].get(command, 0) + 1
            )

        # Update context information
        if context:
            if command not in self.command_contexts:
                self.command_contexts[command] = {}

            for ctx in context.split():
                if ctx:
                    self.command_contexts[command][ctx] = (
                        self.command_contexts[command].get(ctx, 0) + 1
                    )

        # Save history periodically
        if len(self.commands) % 10 == 0:
            self._save_history()

        # Retrain model periodically
        if HAS_SKLEARN and self.model is None and len(self.commands) >= 10:
            self._initialize_model()

    def predict_next_command(
        self, prefix: str = "", context: str = None, max_suggestions: int = 5
    ) -> list[str]:
        """Predict next command based on prefix and context"""
        suggestions = []

        # If we have a prefix, filter by that first
        if prefix:
            # Find commands starting with prefix
            prefix_matches = [cmd for cmd in self.commands if cmd.startswith(prefix)]

            # Sort by frequency
            prefix_suggestions = sorted(
                set(prefix_matches), key=lambda x: self.command_frequencies.get(x, 0), reverse=True
            )

            suggestions.extend(prefix_suggestions[:max_suggestions])

        # If we don't have enough suggestions, use ML model
        if HAS_SKLEARN and self.model and len(suggestions) < max_suggestions:
            try:
                # Vectorize the prefix
                prefix_vec = self.vectorizer.transform([prefix or ""])

                # Get probabilities for each class
                probas = self.model.predict_proba(prefix_vec)[0]

                # Sort by probability
                sorted_indices = probas.argsort()[::-1]
                classes = self.model.classes_

                # Get top predictions
                model_suggestions = []
                for idx in sorted_indices:
                    cmd = classes[idx]
                    if cmd not in suggestions and (not prefix or cmd.startswith(prefix)):
                        model_suggestions.append(cmd)
                        if len(suggestions) + len(model_suggestions) >= max_suggestions:
                            break

                suggestions.extend(model_suggestions)

            except Exception as e:
                logger.error(f"Error predicting with model: {e}")

        # If we still need more suggestions, use sequence information
        if len(suggestions) < max_suggestions and len(self.commands) >= 1:
            last_cmd = self.commands[-1]
            if last_cmd in self.command_sequences:
                seq_commands = self.command_sequences[last_cmd]

                # Sort by frequency
                seq_suggestions = sorted(seq_commands.items(), key=lambda x: x[1], reverse=True)

                for cmd, _ in seq_suggestions:
                    if cmd not in suggestions and (not prefix or cmd.startswith(prefix)):
                        suggestions.append(cmd)
                        if len(suggestions) >= max_suggestions:
                            break

        # If we still need more suggestions, use context information
        if context and len(suggestions) < max_suggestions:
            context_relevance = {}

            for cmd, ctx_dict in self.command_contexts.items():
                if prefix and not cmd.startswith(prefix):
                    continue

                if cmd in suggestions:
                    continue

                # Calculate relevance score
                score = 0
                for ctx_word in context.split():
                    if ctx_word in ctx_dict:
                        score += ctx_dict[ctx_word]

                if score > 0:
                    context_relevance[cmd] = score

            # Sort by relevance
            context_suggestions = sorted(
                context_relevance.items(), key=lambda x: x[1], reverse=True
            )

            for cmd, _ in context_suggestions:
                if cmd not in suggestions:
                    suggestions.append(cmd)
                    if len(suggestions) >= max_suggestions:
                        break

        # If we still don't have enough, add most frequent commands
        if len(suggestions) < max_suggestions:
            freq_suggestions = sorted(
                self.command_frequencies.items(), key=lambda x: x[1], reverse=True
            )

            for cmd, _ in freq_suggestions:
                if cmd not in suggestions and (not prefix or cmd.startswith(prefix)):
                    suggestions.append(cmd)
                    if len(suggestions) >= max_suggestions:
                        break

        return suggestions[:max_suggestions]

    def train(self, force: bool = False) -> dict[str, Any]:
        """
        Train the command prediction model.

        Args:
            force: If True, force retraining even if recent training exists

        Returns:
            Dict containing training status and statistics
        """
        start_time = time.time()

        # Get before stats
        before_stats = {
            "commands_count": len(self.commands),
            "unique_commands": len(self.command_frequencies),
            "sequences_count": len(self.command_sequences),
            "model_trained": self.model is not None,
        }

        log_with_context(
            "info",
            "Starting command predictor training",
            "predictor",
            "training",
            force=force,
            commands_count=before_stats["commands_count"],
        )

        try:
            # Check if we have enough data
            if len(self.commands) < 10:
                return {
                    "success": False,
                    "message": "Insufficient training data (need at least 10 commands)",
                    "before_stats": before_stats,
                    "after_stats": before_stats,
                    "training_time_ms": (time.time() - start_time) * 1000,
                }

            # Check if recent training exists and force is not set
            if not force and hasattr(self, "_last_training_time"):
                time_since_training = time.time() - self._last_training_time
                if time_since_training < 3600:  # Less than 1 hour ago
                    return {
                        "success": False,
                        "message": f"Recent training exists ({time_since_training/60:.1f} minutes ago). Use force=True to retrain",
                        "before_stats": before_stats,
                        "after_stats": before_stats,
                        "training_time_ms": (time.time() - start_time) * 1000,
                    }

            # Retrain the model
            self._initialize_model()
            self._last_training_time = time.time()

            # Get after stats
            after_stats = {
                "commands_count": len(self.commands),
                "unique_commands": len(self.command_frequencies),
                "sequences_count": len(self.command_sequences),
                "model_trained": self.model is not None,
            }

            training_time_ms = (time.time() - start_time) * 1000

            log_with_context(
                "info",
                "Command predictor training completed",
                "predictor",
                "training",
                training_time_ms=training_time_ms,
                unique_commands=after_stats["unique_commands"],
            )

            return {
                "success": True,
                "message": "Command predictor trained successfully",
                "before_stats": before_stats,
                "after_stats": after_stats,
                "training_time_ms": training_time_ms,
            }

        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            log_with_context("error", error_msg, "predictor", "training", error=str(e))

            return {
                "success": False,
                "message": error_msg,
                "before_stats": before_stats,
                "after_stats": before_stats,
                "training_time_ms": (time.time() - start_time) * 1000,
            }


class NaturalLanguageProcessor:
    """Processes natural language commands"""

    def __init__(self, training_file: str = "~/.triad/ai/nl_training.json"):
        self.training_file = os.path.expanduser(training_file)
        self.training_dir = os.path.dirname(self.training_file)
        os.makedirs(self.training_dir, exist_ok=True)

        # Command mappings
        self.command_templates = {}
        self.intent_patterns = {}
        self.entity_patterns = {}

        # Load training data
        self._load_training_data()

        # Initialize ML components
        self.vectorizer = None
        self.classifier = None
        if HAS_SKLEARN:
            self._initialize_models()

    def _load_training_data(self) -> None:
        """Load NL training data"""
        # Define default training data
        default_data = {
            "command_templates": {
                "list_files": "ls {path}",
                "find_files": "find {path} -name {pattern}",
                "create_directory": "mkdir {directory}",
                "remove_file": "rm {file}",
                "show_file": "cat {file}",
                "edit_file": "nano {file}",
                "process_status": "ps aux | grep {process}",
                "disk_usage": "df -h {path}",
                "memory_usage": "free -h",
                "network_status": "netstat -tuln",
                "compress": "tar -czvf {output}.tar.gz {input}",
                "extract": "tar -xzvf {file}",
            },
            "intent_patterns": {
                "list_files": [
                    "list files",
                    "show files",
                    "list directory",
                    "show directory contents",
                    "what files are in",
                ],
                "find_files": [
                    "find files",
                    "search for files",
                    "locate files",
                    "find files named",
                    "search for files with pattern",
                ],
                "create_directory": [
                    "create directory",
                    "make directory",
                    "create folder",
                    "new directory",
                    "make a new folder",
                ],
                "remove_file": [
                    "remove file",
                    "delete file",
                    "remove the file",
                    "delete the file",
                    "get rid of file",
                ],
                "show_file": [
                    "show file",
                    "display file",
                    "show contents of",
                    "display contents of",
                    "what's in the file",
                ],
                "edit_file": [
                    "edit file",
                    "modify file",
                    "change file",
                    "open file for editing",
                    "edit the contents of",
                ],
                "process_status": [
                    "check process",
                    "show processes",
                    "list processes",
                    "find process",
                    "is process running",
                ],
                "disk_usage": [
                    "disk usage",
                    "storage usage",
                    "disk space",
                    "how much disk space",
                    "drive space",
                ],
                "memory_usage": [
                    "memory usage",
                    "ram usage",
                    "how much memory",
                    "show memory",
                    "check ram",
                ],
                "network_status": [
                    "network status",
                    "network connections",
                    "open ports",
                    "listening ports",
                    "check network",
                ],
                "compress": [
                    "compress file",
                    "compress directory",
                    "create archive",
                    "make zip",
                    "tar directory",
                ],
                "extract": [
                    "extract archive",
                    "uncompress file",
                    "extract zip",
                    "unpack archive",
                    "expand file",
                ],
            },
            "entity_patterns": {
                "path": [r"in\s+(.+)", r"at\s+(.+)", r"from\s+(.+)", r"path\s+(.+)"],
                "pattern": [r"named\s+(.+)", r"with name\s+(.+)", r"pattern\s+(.+)"],
                "directory": [r"directory\s+(.+)", r"folder\s+(.+)", r"named\s+(.+)"],
                "file": [r"file\s+(.+)", r"the file\s+(.+)"],
                "process": [r"process\s+(.+)", r"application\s+(.+)", r"program\s+(.+)"],
                "output": [r"as\s+(.+)", r"to\s+(.+)", r"output\s+(.+)"],
                "input": [r"input\s+(.+)", r"source\s+(.+)", r"file\s+(.+)", r"directory\s+(.+)"],
            },
        }

        # Try to load existing training data
        if os.path.exists(self.training_file):
            try:
                with open(self.training_file) as f:
                    training_data = json.load(f)

                self.command_templates = training_data.get("command_templates", {})
                self.intent_patterns = training_data.get("intent_patterns", {})
                self.entity_patterns = training_data.get("entity_patterns", {})

                logger.info("Loaded NL training data")

            except Exception as e:
                logger.error(f"Error loading NL training data: {e}")
                # Fall back to default data
                self.command_templates = default_data["command_templates"]
                self.intent_patterns = default_data["intent_patterns"]
                self.entity_patterns = default_data["entity_patterns"]
        else:
            # Use default data and save it
            self.command_templates = default_data["command_templates"]
            self.intent_patterns = default_data["intent_patterns"]
            self.entity_patterns = default_data["entity_patterns"]

            self._save_training_data()

    def _save_training_data(self) -> None:
        """Save NL training data"""
        try:
            training_data = {
                "command_templates": self.command_templates,
                "intent_patterns": self.intent_patterns,
                "entity_patterns": self.entity_patterns,
            }

            with open(self.training_file, "w") as f:
                json.dump(training_data, f, indent=2)

            logger.debug("NL training data saved")

        except Exception as e:
            logger.error(f"Error saving NL training data: {e}")

    def _initialize_models(self) -> None:
        """Initialize ML models for intent classification"""
        if not HAS_SKLEARN:
            return

        try:
            # Create training data
            intents = []
            patterns = []

            for intent, intent_patterns in self.intent_patterns.items():
                for pattern in intent_patterns:
                    intents.append(intent)
                    patterns.append(pattern)

            if len(intents) < 2:
                return

            # Create vectorizer and classifier
            self.vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
            X = self.vectorizer.fit_transform(patterns)

            self.classifier = LogisticRegression(max_iter=1000)
            self.classifier.fit(X, intents)

            logger.info("NL models initialized")

        except Exception as e:
            logger.error(f"Error initializing NL models: {e}")

    def process_command(self, nl_command: str) -> dict[str, Any]:
        """Process a natural language command"""
        result = {
            "success": False,
            "intent": None,
            "entities": {},
            "command": None,
            "confidence": 0.0,
        }

        # Clean up command
        nl_command = nl_command.lower().strip()
        if not nl_command:
            return result

        # Detect intent
        intent, confidence = self._detect_intent(nl_command)
        if not intent:
            return result

        result["intent"] = intent
        result["confidence"] = confidence

        # Extract entities
        entities = self._extract_entities(nl_command, intent)
        result["entities"] = entities

        # Get command template
        template = self.command_templates.get(intent)
        if not template:
            return result

        # Fill in template
        try:
            # Replace entities in template
            command = template
            for entity, value in entities.items():
                placeholder = f"{{{entity}}}"
                if placeholder in command:
                    command = command.replace(placeholder, value)

            # Check if all placeholders were replaced
            if "{" in command and "}" in command:
                # Some entities are missing
                result["command"] = command  # Return partial command
                result["success"] = False
            else:
                result["command"] = command
                result["success"] = True

        except Exception as e:
            logger.error(f"Error filling command template: {e}")

        return result

    def _detect_intent(self, nl_command: str) -> tuple[str | None, float]:
        """Detect intent from natural language command"""
        # Try ML-based classification if available
        if HAS_SKLEARN and self.classifier and self.vectorizer:
            try:
                # Vectorize the command
                X = self.vectorizer.transform([nl_command])

                # Get predictions and probabilities
                intent = self.classifier.predict(X)[0]
                probas = self.classifier.predict_proba(X)[0]
                confidence = max(probas)

                return intent, confidence

            except Exception as e:
                logger.error(f"Error in ML intent detection: {e}")

        # Fall back to pattern matching
        best_intent = None
        best_score = 0

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                # Calculate simple match score
                pattern_words = set(pattern.split())
                command_words = set(nl_command.split())

                common_words = pattern_words.intersection(command_words)
                if not common_words:
                    continue

                # Score based on word overlap
                score = len(common_words) / max(len(pattern_words), len(command_words))

                if score > best_score:
                    best_score = score
                    best_intent = intent

        return best_intent, best_score

    def _extract_entities(self, nl_command: str, intent: str) -> dict[str, str]:
        """Extract entities from command based on intent"""
        entities = {}

        # Get entities needed for this intent
        template = self.command_templates.get(intent, "")
        required_entities = re.findall(r"{(\w+)}", template)

        # Extract each entity
        for entity in required_entities:
            # Get patterns for this entity
            patterns = self.entity_patterns.get(entity, [])

            for pattern in patterns:
                match = re.search(pattern, nl_command)
                if match:
                    entities[entity] = match.group(1).strip()
                    break

            # If entity not found, try extracting from command words
            if entity not in entities:
                # Use the last word as a fallback for certain entities
                if entity in ["file", "directory", "path"]:
                    words = nl_command.split()
                    if words:
                        entities[entity] = words[-1]

        return entities

    def add_training_example(self, nl_command: str, intent: str, executed_command: str) -> bool:
        """Add a training example to improve NL processing"""
        if not nl_command or not intent or not executed_command:
            return False

        nl_command = nl_command.lower().strip()

        # Update intent patterns
        if intent in self.intent_patterns:
            # Add to existing intent if not already present
            if nl_command not in self.intent_patterns[intent]:
                self.intent_patterns[intent].append(nl_command)
        else:
            # Create new intent
            self.intent_patterns[intent] = [nl_command]

        # Update command template if not exists
        if intent not in self.command_templates:
            # Try to create a template from the executed command
            template = executed_command

            # Look for potential entities
            words = nl_command.split()
            for word in words:
                if word in executed_command and len(word) > 2:
                    # This word appears in both - might be an entity
                    entity_name = self._guess_entity_type(word)
                    template = template.replace(word, f"{{{entity_name}}}")

                    # Add entity pattern
                    if entity_name not in self.entity_patterns:
                        self.entity_patterns[entity_name] = []

                    pattern = f"\\b{word}\\b"
                    if pattern not in self.entity_patterns[entity_name]:
                        self.entity_patterns[entity_name].append(pattern)

            self.command_templates[intent] = template

        # Save training data
        self._save_training_data()

        # Reinitialize ML models
        if HAS_SKLEARN:
            self._initialize_models()

        return True

    def _guess_entity_type(self, word: str) -> str:
        """Guess entity type from word"""
        if word.endswith(".txt") or word.endswith(".py") or "." in word:
            return "file"
        elif "/" in word:
            return "path"
        elif word.startswith("-"):
            return "option"
        else:
            return "arg"


class AIAssistant:
    """Main AI assistant integrating all intelligent components"""

    def __init__(self, data_dir: str = "~/.triad/ai"):
        self.data_dir = os.path.expanduser(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize components
        self.code_engine = CodeCompletionEngine(os.path.join(self.data_dir, "models"))
        self.command_predictor = CommandPredictor(
            os.path.join(self.data_dir, "history/commands.json")
        )
        self.nl_processor = NaturalLanguageProcessor(
            os.path.join(self.data_dir, "nl_training.json")
        )

        # State tracking
        self.current_context = ""
        self.last_command = ""

    def complete_code(self, code_context: str, language: str) -> list[str]:
        """Get code completion suggestions"""
        return self.code_engine.get_completion(code_context, language)

    def predict_command(self, prefix: str = "") -> list[str]:
        """Predict next command based on prefix and history"""
        return self.command_predictor.predict_next_command(prefix, context=self.current_context)

    def process_nl_command(self, nl_command: str) -> dict[str, Any]:
        """Process natural language command"""
        return self.nl_processor.process_command(nl_command)

    def add_executed_command(self, command: str) -> None:
        """Track an executed command"""
        self.command_predictor.add_command(command, self.current_context)
        self.last_command = command

    def add_code_sample(self, code: str, language: str) -> None:
        """Add code sample for training"""
        self.code_engine.add_code_sample(code, language)

    def set_context(self, context: str) -> None:
        """Set current context (e.g. current directory, project)"""
        self.current_context = context

    def provide_feedback(self, nl_command: str, executed_command: str, intent: str = None) -> None:
        """Provide feedback to improve NL processing"""
        if not intent:
            # Try to guess intent from command
            intent = self._guess_intent(executed_command)

        if intent:
            self.nl_processor.add_training_example(nl_command, intent, executed_command)

    def _guess_intent(self, command: str) -> str | None:
        """Guess intent from executed command with enhanced pattern recognition"""
        if not command:
            return None

        command_lower = command.lower()
        command_start = command.split()[0] if command else ""

        # Enhanced command to intent mapping
        command_intent_map = {
            # File operations
            "ls": "list_files",
            "ll": "list_files",
            "dir": "list_files",
            "find": "find_files",
            "locate": "find_files",
            "which": "find_files",
            "mkdir": "create_directory",
            "md": "create_directory",
            "rm": "remove_file",
            "rmdir": "remove_file",
            "del": "remove_file",
            "cat": "show_file",
            "less": "show_file",
            "more": "show_file",
            "head": "show_file",
            "tail": "show_file",
            "nano": "edit_file",
            "vim": "edit_file",
            "vi": "edit_file",
            "emacs": "edit_file",
            "code": "edit_file",
            "cp": "copy_file",
            "copy": "copy_file",
            "mv": "move_file",
            "move": "move_file",
            "chmod": "change_permissions",
            "chown": "change_ownership",
            # Git commands
            "git": "git_operation",
            # Package managers
            "pip": "package_management",
            "pip3": "package_management",
            "npm": "package_management",
            "yarn": "package_management",
            "apt": "package_management",
            "apt-get": "package_management",
            "yum": "package_management",
            "dnf": "package_management",
            "brew": "package_management",
            "conda": "package_management",
            # System monitoring
            "ps": "process_status",
            "top": "process_status",
            "htop": "process_status",
            "df": "disk_usage",
            "du": "disk_usage",
            "lsblk": "disk_usage",
            "free": "memory_usage",
            "vmstat": "memory_usage",
            "netstat": "network_status",
            "ss": "network_status",
            "lsof": "network_status",
            "systemctl": "service_management",
            "service": "service_management",
            "crontab": "scheduling",
            "at": "scheduling",
            # Network diagnostics
            "ping": "network_diagnostic",
            "curl": "network_diagnostic",
            "wget": "network_diagnostic",
            "ssh": "remote_connection",
            "scp": "file_transfer",
            "rsync": "file_transfer",
            "telnet": "network_diagnostic",
            "nslookup": "network_diagnostic",
            "dig": "network_diagnostic",
            # Archive/compression
            "tar": "archive_operation",
            "zip": "compress",
            "unzip": "extract",
            "gzip": "compress",
            "gunzip": "extract",
            "bzip2": "compress",
            "bunzip2": "extract",
            # Python tooling
            "python": "python_execution",
            "python3": "python_execution",
            "py": "python_execution",
            "pytest": "testing",
            "unittest": "testing",
            "coverage": "testing",
            "black": "code_formatting",
            "flake8": "code_analysis",
            "pylint": "code_analysis",
            "mypy": "type_checking",
            "isort": "import_sorting",
            # Development tools
            "make": "build_system",
            "cmake": "build_system",
            "gradle": "build_system",
            "docker": "containerization",
            "kubectl": "container_orchestration",
            "node": "javascript_execution",
            "npm": "package_management",
        }

        # First try direct command mapping
        base_intent = command_intent_map.get(command_start)
        if base_intent:
            # Refine based on command patterns and flags
            return self._refine_intent_with_patterns(base_intent, command_lower)

        # Pattern-based heuristics for complex commands
        intent = self._guess_intent_from_patterns(command_lower)
        if intent:
            return intent

        log_with_context(
            "debug",
            "No intent found for command",
            "assistant",
            "intent_detection",
            command=command_start,
        )
        return None

    def _refine_intent_with_patterns(self, base_intent: str, command: str) -> str:
        """Refine intent based on command patterns and flags"""

        # Git operation refinements
        if base_intent == "git_operation":
            if any(x in command for x in ["clone", "pull", "fetch"]):
                return "git_sync"
            elif any(x in command for x in ["add", "commit", "push"]):
                return "git_commit"
            elif any(x in command for x in ["branch", "checkout", "merge"]):
                return "git_branching"
            elif any(x in command for x in ["status", "log", "diff"]):
                return "git_info"
            return "git_operation"

        # Archive operation refinements
        if base_intent == "archive_operation":
            if "-c" in command or "create" in command:
                return "compress"
            elif "-x" in command or "extract" in command:
                return "extract"
            elif "-t" in command or "list" in command:
                return "list_archive"
            return "archive_operation"

        # Package management refinements
        if base_intent == "package_management":
            if any(x in command for x in ["install", "add"]):
                return "install_package"
            elif any(x in command for x in ["remove", "uninstall", "delete"]):
                return "remove_package"
            elif any(x in command for x in ["update", "upgrade"]):
                return "update_package"
            elif any(x in command for x in ["list", "search", "show"]):
                return "query_package"
            return "package_management"

        return base_intent

    def _guess_intent_from_patterns(self, command: str) -> str | None:
        """Guess intent from command patterns and content"""

        # File extension patterns
        if any(ext in command for ext in [".py", "*.py", "python"]):
            return "python_operation"

        if any(ext in command for ext in [".js", "*.js", ".json", "node"]):
            return "javascript_operation"

        # Flag-based patterns
        if "-rf" in command and any(cmd in command for cmd in ["rm", "delete"]):
            return "force_remove"

        if "grep" in command or "awk" in command or "sed" in command:
            return "text_processing"

        if "|" in command and any(cmd in command for cmd in ["sort", "uniq", "wc"]):
            return "data_processing"

        # Path patterns
        if any(path in command for path in ["/var/log", "/tmp", "/etc"]):
            return "system_administration"

        return None

    def train_models(self, force: bool = False, components: list[str] = ["all"]) -> dict[str, Any]:
        """
        Train all models with enhanced capabilities.

        Args:
            force: Force retraining even if recent training exists
            components: List of components to train ('code', 'commands', 'nl', 'all')

        Returns:
            Dict containing training results for all components
        """
        start_time = time.time()
        results = {
            "success": True,
            "message": "Training completed",
            "components_trained": [],
            "before_stats": {},
            "after_stats": {},
            "training_time_ms": 0,
        }

        # Determine which components to train
        train_all = "all" in components
        train_components = {
            "code": train_all or "code" in components,
            "commands": train_all or "commands" in components,
            "nl": train_all or "nl" in components,
        }

        log_with_context(
            "info",
            "Starting model training",
            "assistant",
            "training",
            components=components,
            force=force,
        )

        # Collect before stats
        results["before_stats"] = self.status()

        try:
            # Train code completion engine
            if train_components["code"]:
                try:
                    self.code_engine.train_models(background=False)
                    results["components_trained"].append("code")
                    log_with_context(
                        "info", "Code engine training completed", "assistant", "training"
                    )
                except Exception as e:
                    log_with_context(
                        "error", f"Code engine training failed: {e}", "assistant", "training"
                    )
                    results["success"] = False

            # Train command predictor
            if train_components["commands"]:
                try:
                    cmd_result = self.command_predictor.train(force=force)
                    if cmd_result["success"]:
                        results["components_trained"].append("commands")
                        log_with_context(
                            "info", "Command predictor training completed", "assistant", "training"
                        )
                    else:
                        log_with_context(
                            "warning",
                            f"Command predictor training failed: {cmd_result['message']}",
                            "assistant",
                            "training",
                        )
                        if "insufficient" in cmd_result["message"].lower():
                            # Not a real failure, just insufficient data
                            pass
                        else:
                            results["success"] = False
                except Exception as e:
                    log_with_context(
                        "error", f"Command predictor training failed: {e}", "assistant", "training"
                    )
                    results["success"] = False

            # Train NL processor
            if train_components["nl"]:
                try:
                    # The NL processor is trained incrementally, just reinitialize models
                    self.nl_processor._initialize_models()
                    results["components_trained"].append("nl")
                    log_with_context(
                        "info", "NL processor training completed", "assistant", "training"
                    )
                except Exception as e:
                    log_with_context(
                        "error", f"NL processor training failed: {e}", "assistant", "training"
                    )
                    results["success"] = False

        except Exception as e:
            log_with_context("error", f"Training failed: {e}", "assistant", "training")
            results["success"] = False
            results["message"] = f"Training failed: {str(e)}"

        # Collect after stats
        results["after_stats"] = self.status()
        results["training_time_ms"] = (time.time() - start_time) * 1000

        if results["success"]:
            results["message"] = (
                f"Training completed successfully for components: {', '.join(results['components_trained'])}"
            )

        return results

    def status(self) -> dict[str, Any]:
        """
        Get comprehensive status of the AI assistant.

        Returns:
            Dict containing detailed status information
        """
        try:
            # Basic capability check
            capabilities = ["command_prediction", "natural_language_processing", "code_completion"]

            # Check model status
            models_loaded = {
                "command_predictor": self.command_predictor.model is not None,
                "nl_classifier": getattr(self.nl_processor, "classifier", None) is not None,
                "code_engine": len(self.code_engine.language_models) > 0,
            }

            # Training readiness
            training_ready = (
                len(self.command_predictor.commands) >= 5  # Minimum command history
                and len(self.nl_processor.intent_patterns) > 0  # Has intent patterns
            )

            # Intent mapping size
            intent_mapping_size = len(self.nl_processor.intent_patterns)

            # Get last training time if available
            last_trained = None
            if hasattr(self.command_predictor, "_last_training_time"):
                last_trained = datetime.fromtimestamp(self.command_predictor._last_training_time)

            return {
                "enabled": True,
                "models_loaded": any(models_loaded.values()),
                "training_ready": training_ready,
                "intent_mapping_size": intent_mapping_size,
                "last_trained": last_trained,
                "capabilities": capabilities,
                "model_details": models_loaded,
                "component_stats": {
                    "commands_in_history": len(self.command_predictor.commands),
                    "unique_commands": len(self.command_predictor.command_frequencies),
                    "intent_patterns": len(self.nl_processor.intent_patterns),
                    "command_templates": len(self.nl_processor.command_templates),
                    "code_models": len(self.code_engine.language_models),
                },
                "ml_availability": {"sklearn": HAS_SKLEARN, "tensorflow": HAS_TENSORFLOW},
            }

        except Exception as e:
            log_with_context("error", f"Error getting status: {e}", "assistant", "status")
            return {
                "enabled": False,
                "models_loaded": False,
                "training_ready": False,
                "intent_mapping_size": 0,
                "last_trained": None,
                "capabilities": [],
                "error": str(e),
            }


def main() -> None:
    """Test the AI assistant"""
    assistant = AIAssistant()

    print("Testing AI Assistant")
    print("===================")

    # Test code completion
    python_code = (
        "def calculate_average(numbers):\n    total = sum(numbers)\n    return total / len"
    )
    completions = assistant.complete_code(python_code, "python")
    print("\nCode Completion Test:")
    print(f"Context: {python_code}")
    print(f"Completions: {completions}")

    # Test command prediction
    assistant.add_executed_command("ls -la")
    assistant.add_executed_command("cd projects")
    assistant.add_executed_command("git status")

    predictions = assistant.predict_command("g")
    print("\nCommand Prediction Test:")
    print("Prefix: 'g'")
    print(f"Predictions: {predictions}")

    # Test NL processing
    nl_result = assistant.process_nl_command("show me what files are in the current directory")
    print("\nNL Processing Test:")
    print("Command: 'show me what files are in the current directory'")
    print(f"Result: {nl_result}")

    print("\nAI Assistant test complete")


if __name__ == "__main__":
    print(
        """
This file has been renamed to assistant_ml.py to follow Python naming conventions.
Please update your imports to use 'assistant_ml' instead of 'assistant-ML'.
"""
    )

 copilot/fix-c1e50cd2-35ad-4991-8bc0-a59778375133
    raise ImportError(
        "The file 'assistant-ML.py' has been renamed to 'assistant_ml.py' to follow Python naming conventions. "
        "Please update your import to: 'from agents.learning.assistant_ml import ...' "
        "instead of 'from agents.learning.assistant-ML import ...'"
    

raise ImportError(
    "The file 'assistant-ML.py' has been renamed to 'assistant_ml.py' to follow Python naming conventions. "
    "Please update your import to: 'from agents.learning.assistant_ml import ...' "
    "instead of 'from agents.learning.assistant-ML import ...'"
 main
