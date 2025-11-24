"""
MIDI Command Synthesizer
Stores MIDI commands as a compact vector and synthesizes music from them.
"""

import numpy as np
from midiutil import MIDIFile
from io import BytesIO
import struct


class MIDICommandSynthesizer:
    """Stores and synthesizes music from MIDI commands."""

    def __init__(self, num_tracks=1, tempo=120):
        """
        Initialize the MIDI synthesizer.

        Args:
            num_tracks: Number of MIDI tracks
            tempo: Tempo in BPM
        """
        self.num_tracks = num_tracks
        self.tempo = tempo
        self.midi_commands = []

    def add_note(self, pitch, duration, velocity=100, track=0, time=0):
        """
        Add a note to the MIDI commands vector.

        Args:
            pitch: MIDI pitch (0-127)
            duration: Duration in beats
            velocity: Note velocity (0-127)
            track: Track number
            time: Start time in beats
        """
        command = {
            'type': 'note_on',
            'pitch': int(np.clip(pitch, 0, 127)),
            'velocity': int(np.clip(velocity, 0, 127)),
            'duration': float(duration),
            'track': int(track),
            'time': float(time)
        }
        self.midi_commands.append(command)
        return self

    def add_control_change(self, controller, value, track=0, time=0):
        """
        Add a control change command.

        Args:
            controller: CC number (0-127)
            value: CC value (0-127)
            track: Track number
            time: Time in beats
        """
        command = {
            'type': 'control_change',
            'controller': int(np.clip(controller, 0, 127)),
            'value': int(np.clip(value, 0, 127)),
            'track': int(track),
            'time': float(time)
        }
        self.midi_commands.append(command)
        return self

    def add_program_change(self, program, track=0, time=0):
        """
        Add a program change command (instrument selection).

        Args:
            program: Program number (0-127)
            track: Track number
            time: Time in beats
        """
        command = {
            'type': 'program_change',
            'program': int(np.clip(program, 0, 127)),
            'track': int(track),
            'time': float(time)
        }
        self.midi_commands.append(command)
        return self

    def get_command_vector(self):
        """
        Get the MIDI commands as a compact numpy vector.
        Each command is encoded as floats.

        Returns:
            numpy array of command data
        """
        vector = []
        for cmd in self.midi_commands:
            if cmd['type'] == 'note_on':
                # Format: [1, pitch, velocity, duration, track, time]
                vector.extend([1, cmd['pitch'], cmd['velocity'],
                              cmd['duration'], cmd['track'], cmd['time']])
            elif cmd['type'] == 'control_change':
                # Format: [2, controller, value, track, time, 0]
                vector.extend([2, cmd['controller'], cmd['value'],
                              cmd['track'], cmd['time'], 0])
            elif cmd['type'] == 'program_change':
                # Format: [3, program, track, time, 0, 0]
                vector.extend([3, cmd['program'], cmd['track'],
                              cmd['time'], 0, 0])
        return np.array(vector, dtype=np.float32)

    def load_from_vector(self, vector):
        """
        Load MIDI commands from a compact numpy vector.

        Args:
            vector: numpy array of command data
        """
        self.midi_commands = []
        vector = np.array(vector, dtype=np.float32)

        i = 0
        while i < len(vector):
            cmd_type = int(vector[i])

            if cmd_type == 1:  # note_on
                self.add_note(
                    pitch=int(vector[i+1]),
                    velocity=int(vector[i+2]),
                    duration=float(vector[i+3]),
                    track=int(vector[i+4]),
                    time=float(vector[i+5])
                )
                i += 6
            elif cmd_type == 2:  # control_change
                self.add_control_change(
                    controller=int(vector[i+1]),
                    value=int(vector[i+2]),
                    track=int(vector[i+3]),
                    time=float(vector[i+4])
                )
                i += 6
            elif cmd_type == 3:  # program_change
                self.add_program_change(
                    program=int(vector[i+1]),
                    track=int(vector[i+2]),
                    time=float(vector[i+3])
                )
                i += 6
            else:
                i += 1

        return self

    def synthesize_to_file(self, filename):
        """
        Synthesize MIDI commands to a MIDI file.

        Args:
            filename: Output filename for the MIDI file
        """
        # Create MIDI object
        midi = MIDIFile(self.num_tracks)

        # Set tempo for all tracks
        for track in range(self.num_tracks):
            midi.addTempo(track, 0, self.tempo)

        # Sort commands by time
        sorted_commands = sorted(self.midi_commands, key=lambda x: x['time'])

        # Process commands
        for cmd in sorted_commands:
            track = cmd['track']
            time = cmd['time']

            if cmd['type'] == 'note_on':
                midi.addNote(
                    track=track,
                    channel=0,
                    pitch=cmd['pitch'],
                    time=time,
                    duration=cmd['duration'],
                    volume=cmd['velocity']
                )
            elif cmd['type'] == 'control_change':
                midi.addControllerEvent(
                    track=track,
                    channel=0,
                    time=time,
                    controller=cmd['controller'],
                    value=cmd['value']
                )
            elif cmd['type'] == 'program_change':
                midi.addProgramChange(
                    track,
                    0,
                    time,
                    cmd['program']
                )

        # Write to file
        with open(filename, 'wb') as output_file:
            midi.writeFile(output_file)

        print(f"MIDI file saved to: {filename}")

    def print_commands(self):
        """Print all stored MIDI commands."""
        print("\nStored MIDI Commands:")
        print("-" * 70)
        for i, cmd in enumerate(self.midi_commands):
            print(f"{i}: {cmd}")
        print("-" * 70)


def demo_simple_melody():
    """Create and synthesize a simple melody."""
    print("\n=== Creating Simple Melody ===")

    synth = MIDICommandSynthesizer(tempo=120)

    # Define a simple melody (C Major scale)
    # C, D, E, F, G, A, B, C (octave up)
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]

    for i, pitch in enumerate(pitches):
        synth.add_note(pitch=pitch, duration=1.0, velocity=100, time=i)

    synth.print_commands()

    # Show command vector
    vector = synth.get_command_vector()
    print(f"\nCommand vector shape: {vector.shape}")
    print(f"Command vector (first 20 elements): {vector[:20]}")

    # Synthesize to file
    synth.synthesize_to_file("output_melody.mid")

    return synth


def demo_chord_progression():
    """Create and synthesize a chord progression."""
    print("\n=== Creating Chord Progression ===")

    synth = MIDICommandSynthesizer(tempo=100)

    # Set instrument to piano
    synth.add_program_change(program=0, track=0, time=0)

    # Define chord progression (C, F, G, C)
    chords = [
        [60, 64, 67],  # C major (C, E, G)
        [65, 69, 72],  # F major (F, A, C)
        [67, 71, 74],  # G major (G, B, D)
        [60, 64, 67],  # C major
    ]

    for chord_idx, chord in enumerate(chords):
        time = chord_idx * 2
        for pitch in chord:
            synth.add_note(pitch=pitch, duration=2.0, velocity=90, time=time)

    synth.print_commands()

    # Show command vector
    vector = synth.get_command_vector()
    print(f"\nCommand vector size: {len(vector)}")
    print(f"Command vector: {vector}")

    # Test loading from vector
    synth2 = MIDICommandSynthesizer(tempo=100)
    synth2.load_from_vector(vector)
    print(f"\nLoaded {len(synth2.midi_commands)} commands from vector")

    # Synthesize to file
    synth.synthesize_to_file("output_chords.mid")

    return synth


def demo_rhythm_pattern():
    """Create and synthesize a rhythm pattern."""
    print("\n=== Creating Rhythm Pattern ===")

    synth = MIDICommandSynthesizer(tempo=140)

    # Set instrument to drums (channel 9 is drums, but we'll use program 0)
    synth.add_program_change(program=0, track=0, time=0)

    # Create a rhythmic pattern with varied notes
    pattern = [
        (60, 0.5),  # Kick-like
        (64, 0.25),  # Hi-hat-like
        (62, 0.5),
        (64, 0.25),
    ]

    for repeat in range(4):
        for note_pitch, duration in pattern:
            time = repeat * 2 + \
                sum([d for _, d in pattern[:pattern.index((note_pitch, duration))]])
            synth.add_note(pitch=note_pitch, duration=duration,
                           velocity=100, time=time)

    synth.print_commands()

    # Show command vector
    vector = synth.get_command_vector()
    print(f"\nCommand vector shape: {vector.shape}")

    # Synthesize to file
    synth.synthesize_to_file("output_rhythm.mid")

    return synth


if __name__ == "__main__":
    print("MIDI Command Synthesizer Demo")
    print("=" * 70)

    # Run demos
    synth1 = demo_simple_melody()
    synth2 = demo_chord_progression()
    synth3 = demo_rhythm_pattern()

    print("\n" + "=" * 70)
    print("All MIDI files have been generated successfully!")
    print("Check for: output_melody.mid, output_chords.mid, output_rhythm.mid")
