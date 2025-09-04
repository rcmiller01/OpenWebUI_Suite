#!/usr/bin/env python3
"""
Direct test of Feeling Engine components
"""

import sys
import os
sys.path.append('src')

from app import SentimentAnalyzer, EmotionDetector, TextCritic

def main():
    print('🧪 Testing Feeling Engine Components...\n')

    # Test 1: Sentiment Analysis
    sentiment_analyzer = SentimentAnalyzer()
    result = sentiment_analyzer.analyze('I feel so sad and depressed. Everything is terrible.')
    print('Sentiment Test (Sad text):')
    print(f'  Sentiment: {result["sentiment"]}')
    print(f'  Confidence: {result["confidence"]:.2f}')
    print(f'  ✅ PASS: Negative sentiment detected' if result['sentiment'] == 'negative' else '❌ FAIL')
    print()

    # Test 2: Emotion Detection
    emotion_detector = EmotionDetector()
    emotions = emotion_detector.detect('I feel so sad and depressed. Everything is terrible.')
    print('Emotion Test (Sad text):')
    print(f'  Emotions: {emotions}')
    print(f'  ✅ PASS: Sadness emotion detected' if 'sadness' in emotions else '❌ FAIL')
    print()

    # Test 3: Text Critique
    text_critic = TextCritic()
    long_text = 'Um, so basically, I was thinking, you know, that we should, like, do something. It is really important, you know.'
    result = text_critic.critique(long_text, 15)
    print('Critique Test (Rambly text):')
    print(f'  Original tokens: {result["original_tokens"]}')
    print(f'  Cleaned tokens: {result["cleaned_tokens"]}')
    print(f'  Changes: {len(result["changes_made"])} modifications')
    print(f'  Cleaned text: "{result["cleaned_text"]}"')
    print(f'  ✅ PASS: Text critiqued and shortened' if result['cleaned_tokens'] <= 15 and result['changes_made'] else '❌ FAIL')
    print()

    print('🎭 Feeling Engine component tests completed!')

if __name__ == "__main__":
    main()
