\version "2.24.3"
        \language "english"
#(set-global-staff-size 12)
\paper {
  #(set-paper-size '(cons (* 71.33866666666665 mm) (* 25 mm)))
  indent = 0\mm
  left-margin = 0\mm
  right-margin = 0\mm
  top-margin = 0\mm
  bottom-margin = 0\mm
  tagline = ##f
  print-page-number = ##f
}

\layout {
  line-width = 71.33866666666665\mm
  ragged-right = ##f
  \context {
    \Score
    \remove "Bar_number_engraver"
    \remove "Time_signature_engraver"
    \remove "Metronome_mark_engraver"
    \override SpacingSpanner.spacing-increment = #4
    \override SpacingSpanner.uniform-stretching = ##t
  }
  \context {
    \Staff
    \remove "Time_signature_engraver"
    \override Flag.stencil = #modern-straight-flag
    \remove "Clef_engraver"
    \override Stem.transparent = ##t
    \accidentalStyle "dodecaphonic"
    \remove "Bar_engraver"
  }
}

\score {
  \new StaffGroup <<
    \override Score.SystemStartBar.collapse-height = 2
    \override Score.SystemStartBar.X-offset = 0
    \override Score.SystemStartBar.color = #(rgb-color 0.51 0.51 0.51)
    \new Staff {
      
      \clef "treble"
      
      fs'4*563/100_\f
    }
  >>
}