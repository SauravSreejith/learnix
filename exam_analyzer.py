import logging
from collections import defaultdict, Counter
from typing import List, Dict, Any
import numpy as np
import random

from database import SessionLocal
from models import ExamQuestion
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

logger = logging.getLogger(__name__)

class ExamAnalyzer:
    def __init__(self):
        logger.info("Initializing ExamAnalyzer with PostgreSQL pgvector...")
        # REVERTED TO HUGGINGFACE
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.MODEL_CONFIG['name'],
            cache_folder=config.MODEL_CONFIG['cache_folder']
        )
        self.is_fitted = True 

    def semantic_search(self, query: str, subject_code: str, modules: List[str] = None,
                        similarity_threshold: float = config.SEARCH_CONFIG['default_similarity_threshold'],
                        top_k: int = config.SEARCH_CONFIG['default_top_k']) -> List[Dict[str, Any]]:
        
        query_vec = self.embeddings.embed_query(query)
        db = SessionLocal()
        try:
            distance_col = ExamQuestion.embedding.cosine_distance(query_vec).label("distance")
            q = db.query(ExamQuestion, distance_col).filter(ExamQuestion.course_code == subject_code.upper())
            
            if modules and len(modules) > 0:
                q = q.filter(ExamQuestion.module_name.in_(modules))
                
            results = q.order_by(distance_col).limit(top_k).all()
            
            output = []
            for row, dist in results:
                sim = 1.0 - float(dist)
                if sim >= similarity_threshold:
                    output.append({
                        "id": row.id,
                        "question": row.question,
                        "topic": row.topic,
                        "marks": row.marks,
                        "module": row.module_name,
                        "course_code": row.course_code,
                        "similarity_score": sim
                    })
            return output
        finally:
            db.close()

    def get_topic_analysis(self, subject_code: str, min_frequency: int = 2) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            questions = db.query(ExamQuestion).filter(ExamQuestion.course_code == subject_code.upper()).all()
            
            topic_groups = defaultdict(list)
            for q in questions:
                topic_groups[q.topic].append(q)

            analyzed_topics = []
            for topic_name, q_list in topic_groups.items():
                if len(q_list) >= min_frequency:
                    total_marks = sum(float(q.marks) for q in q_list)
                    analyzed_topics.append({
                        'topic': topic_name,
                        'frequency': len(q_list),
                        'total_marks': total_marks,
                        'average_marks': round(total_marks / len(q_list), 2) if q_list else 0,
                        'exams': list(set(q.source_file for q in q_list))
                    })
            return sorted(analyzed_topics, key=lambda x: x['frequency'], reverse=True)
        finally:
            db.close()

    def get_stats(self, subject_code: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            questions = db.query(ExamQuestion).filter(ExamQuestion.course_code == subject_code.upper()).all()
            if not questions: return {'total_questions': 0, 'total_exams': 0, 'total_topics': 0, 'modules': []}

            return {
                'total_questions': len(questions),
                'total_exams': len(set(q.source_file for q in questions)),
                'total_topics': len(set(q.topic for q in questions)),
                'modules': sorted(list(set(q.module_name for q in questions if q.module_name)))
            }
        finally:
            db.close()

    def _calculate_topic_weights(self, subject_code: str) -> Dict[str, Dict[str, Any]]:
        db = SessionLocal()
        try:
            questions = db.query(ExamQuestion).filter(ExamQuestion.course_code == subject_code.upper()).all()
            topic_stats = defaultdict(lambda: {'marks': []})
            
            for q in questions:
                if q.topic == 'Untagged' or not q.topic: continue
                topic_stats[q.topic]['marks'].append(float(q.marks))

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
        finally:
            db.close()

    def get_pass_strategy(self, subject_code: str, studied_topics: List[str], target_external_marks: int) -> Dict[str, Any]:
        all_topic_weights = self._calculate_topic_weights(subject_code)
        current_score = sum(
            all_topic_weights[topic]['average_marks'] for topic in studied_topics if topic in all_topic_weights)
        score_deficit = target_external_marks - current_score

        if score_deficit <= 0:
            return {'summary': "You're on track!", 'strategy': [], 'total_marks_from_strategy': 0}

        candidate_topics = {t: d for t, d in all_topic_weights.items() if t not in studied_topics}
        if not candidate_topics:
            return {'summary': "No more topics to study.", 'strategy': [], 'total_marks_from_strategy': 0}

        SCALE = 100 
        target = int(score_deficit * SCALE)
        dp = {0: ((0, 0.0), [])} 

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

        if not best_topics and dp:
            best_topics = dp[max(dp.keys())][1]

        strategy_items = sorted([
            {'topic': t, 'avg_marks': candidate_topics[t]['average_marks']} for t in best_topics
        ], key=lambda x: x['avg_marks'], reverse=True)
        
        gain = 0
        for s in strategy_items:
            gain += s['avg_marks']
            s['cumulative_marks'] = round(gain, 2)

        return {
            'summary': f"Using DP optimization, to reach your target of {target_external_marks}, focus on these topics.",
            'strategy': strategy_items,
            'total_marks_from_strategy': round(gain, 2)
        }

    def run_pass_simulation(self, subject_code: str, studied_topics: List[str], target_marks: int) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            questions = db.query(ExamQuestion).filter(ExamQuestion.course_code == subject_code.upper()).all()
            unique_exams = set(q.source_file for q in questions)
            total_papers = len(unique_exams)
            
            if total_papers == 0: return {'error': 'Not enough data for simulation.'}

            topic_profiles = defaultdict(lambda: {'papers': set(), 'marks_options': []})
            for q in questions:
                if q.topic == 'Untagged' or not q.topic: continue
                if float(q.marks) > 0:
                    topic_profiles[q.topic]['marks_options'].append(float(q.marks))
                    topic_profiles[q.topic]['papers'].add(q.source_file)

            simulation_data = {
                topic: {
                    'probability': len(data['papers']) / total_papers,
                    'marks_options': data['marks_options'] or [0]
                } for topic, data in topic_profiles.items()
            }

            scores = []
            for _ in range(config.PASS_CONFIG['num_simulations']):
                exam_score = 0
                for topic, data in simulation_data.items():
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
        finally:
            db.close()

    def get_module_distribution(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        return dict(Counter(q['module'] for q in search_results))

    def get_marks_distribution(self, search_results: List[Dict[str, Any]]) -> Dict[str, int]:
        return dict(Counter(str(q['marks']) for q in search_results))