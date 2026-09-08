/**
 * Voice Assistant Helper using Web Speech API (STT) and SpeechSynthesis (TTS)
 */

export class VoiceAssistant {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.recognition = null;
    this.isListening = false;
    this.initRecognition();
  }

  initRecognition() {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';
    }
  }

  startListening(onResult, onEnd, onError) {
    if (!this.recognition) {
      if (onError) onError('Speech Recognition is not supported in this browser. Please use Google Chrome, Edge, or text input.');
      return;
    }

    try {
      this.isListening = true;
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (onResult) onResult(transcript);
      };

      this.recognition.onerror = (event) => {
        this.isListening = false;
        if (onError) onError(event.error);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (onEnd) onEnd();
      };

      this.recognition.start();
    } catch (err) {
      this.isListening = false;
      if (onError) onError(err.message);
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  speak(text, onStart, onEnd) {
    if (!this.synth) return;

    // Cancel ongoing speech
    this.synth.cancel();

    // Clean markdown formatting before speaking
    const cleanText = text
      .replace(/[*_#`~\[\]\(\)]/g, '')
      .replace(/https?:\/\/[^\s]+/g, 'link')
      .replace(/⚠️/g, 'Warning')
      .replace(/✅/g, 'Done')
      .slice(0, 400); // Keep spoken output concise

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = this.synth.getVoices();
    const englishVoice = voices.find(v => (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('David') || v.lang.startsWith('en')));
    if (englishVoice) {
      utterance.voice = englishVoice;
    }

    if (onStart) utterance.onstart = onStart;
    if (onEnd) utterance.onend = onEnd;

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
    }
  }
}

export const voiceAssistant = new VoiceAssistant();
