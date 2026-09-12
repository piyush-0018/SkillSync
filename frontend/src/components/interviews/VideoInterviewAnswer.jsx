import {
  AlertCircle,
  Camera,
  CheckCircle2,
  Clock3,
  Download,
  LoaderCircle,
  Mic,
  Play,
  RotateCcw,
  ShieldCheck,
  Square,
  Video,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

const PREPARATION_SECONDS = 30
const ANSWER_SECONDS = 120

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function recorderOptions() {
  const candidates = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']
  const mimeType = candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate))
  return mimeType ? { mimeType } : undefined
}

export default function VideoInterviewAnswer({ question, isSubmitting, onSubmit }) {
  const liveVideoRef = useRef(null)
  const streamRef = useRef(null)
  const recorderRef = useRef(null)
  const recognitionRef = useRef(null)
  const chunksRef = useRef([])
  const finalTranscriptRef = useRef('')
  const recordingRef = useRef(false)
  const recordingUrlRef = useRef('')
  const [phase, setPhase] = useState('requesting')
  const [secondsLeft, setSecondsLeft] = useState(PREPARATION_SECONDS)
  const [transcript, setTranscript] = useState('')
  const [recordingUrl, setRecordingUrl] = useState('')
  const [deviceError, setDeviceError] = useState('')
  const [speechAvailable, setSpeechAvailable] = useState(() => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition))

  const stopRecording = useCallback(() => {
    if (!recordingRef.current) return
    recordingRef.current = false
    try {
      recognitionRef.current?.stop()
    } catch {
      // Speech recognition may already have ended after a browser timeout.
    }
    if (recorderRef.current?.state !== 'inactive') recorderRef.current?.stop()
  }, [])

  const startRecording = useCallback(() => {
    const stream = streamRef.current
    if (!stream?.active) {
      setDeviceError('The camera connection was lost. Reload this page and allow device access again.')
      return
    }

    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
    setRecordingUrl('')
    setTranscript('')
    finalTranscriptRef.current = ''
    chunksRef.current = []

    const recorder = new MediaRecorder(stream, recorderOptions())
    recorderRef.current = recorder
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data)
    }
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'video/webm' })
      const url = URL.createObjectURL(blob)
      recordingUrlRef.current = url
      setRecordingUrl(url)
      setTranscript((current) => current.trim() || finalTranscriptRef.current.trim())
      setPhase('review')
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-IN'
      recognition.onresult = (event) => {
        let interimTranscript = ''
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          const words = event.results[index][0].transcript
          if (event.results[index].isFinal) finalTranscriptRef.current += `${words} `
          else interimTranscript += words
        }
        setTranscript(`${finalTranscriptRef.current}${interimTranscript}`.trim())
      }
      let recognitionFailed = false
      recognition.onerror = (event) => {
        if (event.error === 'no-speech') return
        recognitionFailed = true
        setSpeechAvailable(false)
      }
      recognition.onend = () => {
        if (!recordingRef.current || recognitionFailed) return
        try {
          recognition.start()
        } catch {
          // Some browsers enforce a delay before recognition can restart.
        }
      }
      recognitionRef.current = recognition
      try {
        recognition.start()
      } catch {
        recognitionRef.current = null
      }
    }

    recordingRef.current = true
    recorder.start(500)
    setSecondsLeft(ANSWER_SECONDS)
    setPhase('recording')
  }, [])

  useEffect(() => {
    let cancelled = false

    async function connectDevices() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: { echoCancellation: true, noiseSuppression: true },
        })
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        if (liveVideoRef.current) liveVideoRef.current.srcObject = stream
        setPhase('ready')
      } catch (error) {
        const message = error?.name === 'NotAllowedError'
          ? 'Camera or microphone permission was blocked. Allow both devices in your browser settings and reload this page.'
          : 'SkillSync could not connect to your camera and microphone. Check that another application is not using them.'
        setDeviceError(message)
        setPhase('error')
      }
    }

    connectDevices()
    return () => {
      cancelled = true
      recordingRef.current = false
      if (recorderRef.current?.state === 'recording') {
        recorderRef.current.onstop = null
        recorderRef.current.stop()
      }
      try {
        recognitionRef.current?.stop()
      } catch {
        // Recognition may already be inactive.
      }
      streamRef.current?.getTracks().forEach((track) => track.stop())
      if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
    }
  }, [])

  useEffect(() => {
    if (phase !== 'preparing' && phase !== 'recording') return undefined
    const timer = window.setInterval(() => {
      setSecondsLeft((current) => {
        if (current > 1) return current - 1
        window.clearInterval(timer)
        if (phase === 'preparing') startRecording()
        else stopRecording()
        return 0
      })
    }, 1000)
    return () => window.clearInterval(timer)
  }, [phase, startRecording, stopRecording])

  function beginPreparation() {
    setSecondsLeft(PREPARATION_SECONDS)
    setPhase('preparing')
  }

  function retake() {
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
    recordingUrlRef.current = ''
    setRecordingUrl('')
    setTranscript('')
    finalTranscriptRef.current = ''
    setSecondsLeft(PREPARATION_SECONDS)
    setPhase('ready')
  }

  const transcriptReady = transcript.trim().length >= 2

  return (
    <section className="mt-7 overflow-hidden rounded-3xl border bg-[var(--surface-elevated)] shadow-[0_22px_55px_-42px_rgba(15,23,42,.7)]">
      <div className="border-b px-5 py-5 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{question.focus_area}</span>
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500"><Video size={14} />Video response · Question {question.sequence_number}</span>
        </div>
        <h2 className="mt-4 max-w-4xl text-xl font-semibold leading-8 tracking-[-0.02em] sm:text-2xl">{question.question_text}</h2>
      </div>

      <div className="grid lg:grid-cols-[minmax(0,1.45fr)_minmax(300px,.75fr)]">
        <div className="bg-slate-950 p-3 sm:p-5">
          <div className="relative aspect-video overflow-hidden rounded-2xl bg-black shadow-2xl">
            {recordingUrl ? (
              <video src={recordingUrl} controls playsInline className="h-full w-full object-cover" aria-label="Recorded interview answer" />
            ) : (
              <video ref={liveVideoRef} autoPlay muted playsInline className="h-full w-full -scale-x-100 object-cover" aria-label="Live camera preview" />
            )}

            {phase === 'requesting' && <div className="absolute inset-0 grid place-items-center bg-slate-950 text-center text-white"><div><LoaderCircle className="mx-auto animate-spin text-indigo-400" /><p className="mt-3 text-sm font-medium">Connecting camera and microphone…</p></div></div>}
            {phase === 'error' && <div className="absolute inset-0 grid place-items-center bg-slate-950 p-7 text-center text-white"><div><AlertCircle className="mx-auto text-rose-400" /><p className="mt-3 max-w-md text-sm leading-6 text-slate-300">{deviceError}</p></div></div>}
            {phase === 'preparing' && <div className="absolute inset-0 grid place-items-center bg-slate-950/72 text-center text-white backdrop-blur-[2px]"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-300">Prepare your answer</p><strong className="mt-2 block text-6xl tabular-nums">{secondsLeft}</strong><p className="mt-2 text-sm text-slate-300">Recording starts automatically</p></div></div>}
            {phase === 'recording' && <div className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-black/65 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur"><span className="h-2.5 w-2.5 animate-pulse rounded-full bg-rose-500" />REC · {formatTime(secondsLeft)}</div>}
            {(phase === 'ready' || phase === 'preparing' || phase === 'recording') && <div className="absolute bottom-3 right-3 flex gap-2"><span className="grid h-8 w-8 place-items-center rounded-full bg-black/55 text-white backdrop-blur" title="Camera active"><Camera size={14} /></span><span className="grid h-8 w-8 place-items-center rounded-full bg-black/55 text-white backdrop-blur" title="Microphone active"><Mic size={14} /></span></div>}
          </div>
          <p className="mt-3 flex items-center gap-2 px-1 text-xs leading-5 text-slate-400"><ShieldCheck size={14} className="shrink-0 text-emerald-400" />The video stays in browser memory and is removed when you submit, retake, or leave. Live transcription uses your browser&apos;s speech service.</p>
        </div>

        <div className="flex min-h-72 flex-col p-5 sm:p-6">
          {phase === 'ready' && <><div className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-300"><CheckCircle2 size={20} /></div><h3 className="mt-4 font-semibold">Camera check complete</h3><p className="mt-2 text-sm leading-6 text-slate-500">You will have 30 seconds to prepare, followed by up to 2 minutes to answer.</p><button type="button" onClick={beginPreparation} className="button-primary mt-auto gap-2"><Clock3 size={16} />Begin preparation</button></>}

          {phase === 'preparing' && <><h3 className="font-semibold">Think before you speak</h3><p className="mt-2 text-sm leading-6 text-slate-500">Outline two or three points. Use a concrete example and explain your reasoning.</p><button type="button" onClick={startRecording} className="button-primary mt-auto gap-2"><Play size={16} fill="currentColor" />Start answering now</button></>}

          {phase === 'recording' && <><h3 className="font-semibold">Answer in progress</h3><p className="mt-2 text-sm leading-6 text-slate-500">Look at the camera, speak naturally, and focus on the substance of your answer.</p><div className="mt-4 rounded-xl bg-[var(--surface-subtle)] p-3 text-xs leading-5 text-slate-500"><p className="font-semibold text-[var(--text-primary)]">Live transcript</p><p className="mt-1 line-clamp-4">{transcript || (speechAvailable ? 'Listening…' : 'Automatic transcription is unavailable in this browser. You can type the transcript after recording.')}</p></div><button type="button" onClick={stopRecording} className="button-secondary mt-auto gap-2"><Square size={15} fill="currentColor" />Stop recording</button></>}

          {phase === 'review' && <><div className="flex items-center justify-between gap-3"><div><h3 className="font-semibold">Review your response</h3><p className="mt-1 text-xs text-slate-500">Edit the transcript so it accurately reflects what you said.</p></div><a href={recordingUrl} download={`skillsync-answer-${question.sequence_number}.webm`} className="icon-button" title="Download recording" aria-label="Download recording"><Download size={17} /></a></div><label htmlFor={`video-transcript-${question.id}`} className="mt-4 text-xs font-semibold">Answer transcript</label><textarea id={`video-transcript-${question.id}`} value={transcript} onChange={(event) => setTranscript(event.target.value.slice(0, 10000))} disabled={isSubmitting} placeholder="Enter or correct the transcript of your recorded answer…" className="mt-2 min-h-36 w-full resize-y rounded-xl border bg-[var(--surface)] p-3 text-sm leading-6 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/15 disabled:opacity-60" /><p className="mt-2 text-[11px] leading-4 text-slate-400">SkillSync evaluates this transcript. It does not score your face, appearance, accent, or emotions.</p><div className="mt-4 grid gap-2 sm:grid-cols-2"><button type="button" onClick={retake} disabled={isSubmitting} className="button-secondary gap-2"><RotateCcw size={15} />Retake</button><button type="button" onClick={() => onSubmit(transcript.trim())} disabled={!transcriptReady || isSubmitting} className="button-primary gap-2 disabled:opacity-50">{isSubmitting ? <><LoaderCircle size={15} className="animate-spin" />Evaluating…</> : 'Submit response'}</button></div></>}

          {phase === 'requesting' && <div className="m-auto text-center"><LoaderCircle className="mx-auto animate-spin text-indigo-500" /><p className="mt-3 text-sm text-slate-500">Preparing your interview room…</p></div>}
          {phase === 'error' && <div className="m-auto text-center"><AlertCircle className="mx-auto text-rose-500" /><h3 className="mt-3 font-semibold">Devices unavailable</h3><p className="mt-2 text-sm leading-6 text-slate-500">Update the site permission, then reload this page. Your interview session will remain active.</p></div>}
        </div>
      </div>
    </section>
  )
}
