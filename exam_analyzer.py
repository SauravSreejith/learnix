import json
import os
import pickle
import logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

import numpy as np
import random
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExamAnalyzer:
    """
    Intelligent exam analysis engine that can process multiple exam formats.
    """

    def __init__(self):
        model_cfg = config.MODEL_CONFIG
        logger.info(f"Loading sentence transformer model: {model_cfg['name']}")
        self.model = SentenceTransformer(model_cfg['name'], cache_folder=model_cfg['cache_folder'])
        self.model_name = model_cfg['name']
        self.cache_dir = model_cfg['cache_folder']
        os.makedirs(self.cache_dir, exist_ok=True)

        self.questions_data: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.is_fitted = False
        self.data_hash: Optional[str] = None
        self.simulation_data: Optional[Dict[str, Any]] = None

    def load_json_files(self, folder_path: str) -> None:
        logger.info(f"Recursively loading JSON files from: {folder_path}")
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        json_files = list(Path(folder_path).rglob('*.json'))
        if not json_files:
            raise ValueError(f"No JSON files found in {folder_path}")

        logger.info(f"Found {len(json_files)} JSON files")
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    exam_data = json.load(f)
                    filename = os.path.relpath(file_path, folder_path)

                    # --- FORMAT DETECTION LOGIC ---
                    if isinstance(exam_data, dict) and 'questions' in exam_data:
                        logger.info(f"Detected KTU format for {filename}")
                        self._process_ktu_exam_data(exam_data, filename)
                    elif isinstance(exam_data, list) and exam_data:
                        logger.info(f"Detected CBSE format for {filename}")
                        self._process_cbse_exam_data(exam_data, filename)
                    else:
                        logger.warning(f"Skipping unrecognized JSON format in {filename}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

        self.data_hash = self._generate_data_hash()
        logger.info(f"Successfully loaded {len(self.questions_data)} questions from all sources")

    def _process_ktu_exam_data(self, exam_data: Dict[str, Any], filename: str) -> None:
        course_code = exam_data.get('courseCode', 'Unknown').strip().upper().replace(" ", "")
        for idx, question_obj in enumerate(exam_data.get('questions', [])):
            processed_question = {
                'id': f"{filename}_{idx}",
                'question': question_obj.get('question', '').strip(),
                'topic': question_obj.get('topic', 'Untagged').strip(),
                'marks': question_obj.get('marks', 0),
                'module': question_obj.get('module', 'Unknown'),
                'course_code': course_code,
                'source_file': filename
            }
            if processed_question['question']:
                self.questions_data.append(processed_question)

    def _process_cbse_exam_data(self, exam_data_list: List[Dict[str, Any]], filename: str) -> None:
        for idx, question_obj in enumerate(exam_data_list):
            subject = question_obj.get('subject', 'Unknown').strip().upper().replace(" ", "")
            grade = question_obj.get('class', '').strip()

            # Create a synthetic course code (e.g., SCIENCE10)
            course_code = f"{subject}{grade}"

            processed_question = {
                'id': f"{filename}_{idx}",
                'question': question_obj.get('question_text', '').strip(),
                # --- THIS IS THE CORRECTED LINE ---
                # It now reads the 'topic' field if it exists, otherwise defaults to 'Untagged'.
                'topic': question_obj.get('topic', 'Untagged').strip(),
                'marks': question_obj.get('marks', 0),
                'module': question_obj.get('section', 'Unknown'),  # Using 'section' as 'module'
                'course_code': course_code,
                'source_file': filename
            }
            if processed_question['question']:
                self.questions_data.append(processed_question)

    # --- Caching and Embedding ---
    def _generate_data_hash(self) -> str:
        import hashlib
        data_str = json.dumps([q['question'] for q in self.questions_data], sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _save_cache(self) -> None:
        pass

    def _load_cache(self) -> bool:
        return False

    def build_embeddings(self) -> None:
        if not self.questions_data:
            logger.warning("No questions loaded. Embeddings will not be built.")
            self.is_fitted = False
            return
        logger.info("Building embeddings for all questions...")
        question_texts = [q['question'] for q in self.questions_data]
        self.embeddings = self.model.encode(question_texts, convert_to_tensor=False, show_progress_bar=True)
        self.is_fitted = True
        logger.info(f"Built embeddings for {len(question_texts)} questions")

    # --- Filtering Helper ---
    def _get_filtered_indices(self, subject_code: str) -> List[int]:
        """Helper to get indices of questions matching a subject code."""
        return [
            i for i, q in enumerate(self.questions_data)
            if q['course_code'] == subject_code.upper()
        ]

    # --- Analysis Methods (No changes needed below this line) ---
    def semantic_search(self, query: str, subject_code: str, modules: List[str] = None,
                        similarity_threshold: float = config.SEARCH_CONFIG['default_similarity_threshold'],
                        top_k: int = config.SEARCH_CONFIG['default_top_k']) -> List[Dict[str, Any]]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")

        base_indices = self._get_filtered_indices(subject_code)
        target_indices = [
            i for i in base_indices
            if not modules or self.questions_data[i]['module'] in modules
        ]

        if not target_indices: return []

        subset_embeddings = self.embeddings[target_indices]
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, subset_embeddings)[0]

        valid_indices = np.where(similarities >= similarity_threshold)[0]
        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
        top_indices_subset = sorted_indices[:top_k]

        results = []
        for subset_idx in top_indices_subset:
            original_idx = target_indices[subset_idx]
            question_data = self.questions_data[original_idx].copy()
            question_data['similarity_score'] = float(similarities[subset_idx])
            results.append(question_data)
        return results

    def get_topic_analysis(self, subject_code: str, min_frequency: int = 2) -> List[Dict[str, Any]]:
        target_indices = self._get_filtered_indices(subject_code)
        if not target_indices: return []

        topic_groups = defaultdict(list)
        for idx in target_indices:
            topic_groups[self.questions_data[idx]['topic']].append(idx)

        analyzed_topics = []
        for topic_name, indices in topic_groups.items():
            if len(indices) >= min_frequency:
                topic_questions = [self.questions_data[i] for i in indices]
                total_marks = sum(float(q.get('marks', 0)) for q in topic_questions)
                analyzed_topics.append({
                    'topic': topic_name,
                    'frequency': len(topic_questions),
                    'total_marks': total_marks,
                    'average_marks': round(total_marks / len(topic_questions), 2) if topic_questions else 0,
                    'exams': list(set(self.questions_data[i].get('source_file', 'N/A') for i in indices))
                })
        return sorted(analyzed_topics, key=lambda x: x['frequency'], reverse=True)

    def get_stats(self, subject_code: str) -> Dict[str, Any]:
        target_indices = self._get_filtered_indices(subject_code)
        if not target_indices: return {'total_questions': 0, 'total_exams': 0, 'total_topics': 0}

        subject_questions = [self.questions_data[i] for i in target_indices]
        return {
            'total_questions': len(subject_questions),
            'total_exams': len(set(q.get('source_file') for q in subject_questions)),
            'total_topics': len(set(q['topic'] for q in subject_questions)),
            'modules': sorted(list(set(q['module'] for q in subject_questions)))
        }

    def _calculate_topic_weights(self, subject_code: str) -> Dict[str, Dict[str, Any]]:
        target_indices = self._get_filtered_indices(subject_code)
        subject_questions = [self.questions_data[i] for i in target_indices]

        topic_stats = defaultdict(lambda: {'marks': []})
        for q in subject_questions:
            topic = q.get('topic', 'Untagged')
            if topic == 'Untagged': continue
            try:
                topic_stats[topic]['marks'].append(float(q.get('marks', 0)))
            except (ValueError, TypeError):
                pass

        weighted_topics = {}
        for topic, data in topic_stats.items():
            if not data['marks']: continue
            avg_marks = np.mean(data['marks'])
            weighted_topics[topic] = {
                'average_marks': round(avg_marks, 2),
                'frequency': len(data['marks']),
                'strategic_value': round(avg_marks * len(data['marks']), 2)
            }
        return weighted_topics

    def get_pass_strategy(self, subject_code: str, studied_topics: List[str], target_external_marks: int) -> Dict[str, Any]:
        all_topic_weights = self._calculate_topic_weights(subject_code)
        current_score = sum(
            all_topic_weights[topic]['average_marks'] for topic in studied_topics if topic in all_topic_weights)
        score_deficit = target_external_marks - current_score

        if score_deficit <= 0:
            return {'summary': "You're on track!", 'strategy': []}

        candidate_topics = {t: d for t, d in all_topic_weights.items() if t not in studied_topics}
        if not candidate_topics:
            return {'summary': "No more topics to study.", 'strategy': [], 'total_marks_from_strategy': 0}

        # DP Knapsack: min "number of topics" to achieve >= score_deficit, tie-breaking by max strategic_value
        SCALE = 10
        target = int(score_deficit * SCALE)
        dp = {0: ((0, 0.0), [])}  # marks -> ((num_topics, -total_strategic_value), [topics])

        for topic, data in candidate_topics.items():
            val = int(data['average_marks'] * SCALE)
            cost_tuple = (1, -data.get('strategic_value', 0))

            current_dp = list(dp.items())
            for current_val, ((current_cnt, current_strat), current_topics) in current_dp:
                new_val = current_val + val
                new_cost = (current_cnt + cost_tuple[0], current_strat + cost_tuple[1])
                
                if new_val not in dp or new_cost < dp[new_val][0]:
                    dp[new_val] = (new_cost, current_topics + [topic])

        best_cost = (float('inf'), float('inf'))
        best_topics = []
        for val, (cost, topics) in dp.items():
            if val >= target:
                if cost < best_cost:
                    best_cost = cost
                    best_topics = topics

        # Fallback to all remaining topics if target is unreachable
        if not best_topics and dp:
            best_topics = dp[max(dp.keys())][1]

        # Output formatting
        strategy_items = []
        for topic in best_topics:
            strategy_items.append({
                'topic': topic,
                'avg_marks': candidate_topics[topic]['average_marks']
            })

        # Sort by higher value first
        strategy_items = sorted(strategy_items, key=lambda x: x['avg_marks'], reverse=True)
        
        gain = 0
        final_strategy = []
        for s in strategy_items:
            gain += s['avg_marks']
            s['cumulative_marks'] = round(gain, 2)
            final_strategy.append(s)

        return {
            'summary': f"Using DP optimization, to reach your target of {target_external_marks}, focus on these topics.",
            'strategy': final_strategy,
            'total_marks_from_strategy': round(gain, 2)
        }

    def _prepare_simulation_data(self, subject_code: str) -> None:
        target_indices = self._get_filtered_indices(subject_code)
        subject_questions = [self.questions_data[i] for i in target_indices]

        unique_exams = set(q.get('source_file') for q in subject_questions)
        total_papers = len(unique_exams)
        if total_papers == 0: self.simulation_data = {}; return

        topic_profiles = defaultdict(lambda: {'papers': set(), 'marks_options': []})
        for q in subject_questions:
            topic = q.get('topic', 'Untagged')
            if topic == 'Untagged': continue
            try:
                marks = float(q.get('marks', 0))
                if marks > 0:
                    topic_profiles[topic]['marks_options'].append(marks)
                    topic_profiles[topic]['papers'].add(q.get('source_file'))
            except (ValueError, TypeError):
                continue

        self.simulation_data = {}
        for topic, data in topic_profiles.items():
            self.simulation_data[topic] = {
                'probability': len(data['papers']) / total_papers,
                'marks_options': data['marks_options'] or [0]
            }

    def run_pass_simulation(self, subject_code: str, studied_topics: List[str], target_marks: int) -> Dict[str, Any]:
        self._prepare_simulation_data(subject_code)
        if not self.simulation_data: return {'error': 'Not enough data for simulation.'}

        scores = []
        for _ in range(config.PASS_CONFIG['num_simulations']):
            exam_score = 0
            for topic, data in self.simulation_data.items():
                if random.random() < data['probability'] and topic in studied_topics:
                    exam_score += random.choice(data['marks_options'])
            scores.append(exam_score)

        scores_array = np.array(scores)
        pass_prob = np.sum(scores_array >= target_marks) / config.PASS_CONFIG['num_simulations']

        return {
            'pass_probability': round(pass_prob, 2),
            'average_expected_marks': round(np.mean(scores_array), 2),
            'summary': f"With the topics you've studied, you have a {round(pass_prob * 100)}% chance of passing."
        }

    def get_module_distribution(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        return dict(Counter(q['module'] for q in search_results))

    def get_marks_distribution(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        return dict(Counter(str(q['marks']) for q in search_results))