"""VoiceClone CLI — Command-line interface for voice cloning

Designed to be friendly and accessible, with rich output,
progress bars, and clear error messages.

Usage:
    voiceclone clone maria                  # Clone from microphone
    voiceclone clone maria --from audio.wav # Clone from file
    voiceclone speak "Hola" --voice maria   # Synthesize speech
    voiceclone voices                       # List cloned voices
    voiceclone server                       # Start API server

See: ~/clawd/projects/voiceclone/mockups/cli-mockups.md
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("voiceclone")

# Default paths
DEFAULT_DIR = Path.home() / ".voiceclone"


def get_console():
    """Lazy import Rich console to avoid import errors if not installed"""
    try:
        from rich.console import Console
        return Console()
    except ImportError:
        return None


def print_header(title: str) -> None:
    """Print a styled header"""
    console = get_console()
    if console:
        from rich.panel import Panel
        console.print(Panel(f"🎤 {title}", style="bold cyan"))
    else:
        click.echo(f"\n🎤 {title}")
        click.echo("─" * 40)


def print_success(msg: str) -> None:
    console = get_console()
    if console:
        console.print(f"  ✅ {msg}", style="green")
    else:
        click.echo(f"  ✅ {msg}")


def print_error(msg: str) -> None:
    console = get_console()
    if console:
        console.print(f"  ❌ {msg}", style="bold red")
    else:
        click.echo(f"  ❌ {msg}", err=True)


def print_warning(msg: str) -> None:
    console = get_console()
    if console:
        console.print(f"  ⚠️  {msg}", style="yellow")
    else:
        click.echo(f"  ⚠️  {msg}")


def print_info(msg: str) -> None:
    console = get_console()
    if console:
        console.print(f"  {msg}", style="dim")
    else:
        click.echo(f"  {msg}")


def get_manager(device: Optional[str] = None, quiet: bool = False):
    """Initialize and return the EngineManager"""
    from voice_engine.manager import EngineManager

    manager = EngineManager(device=device)
    
    if not quiet:
        console = get_console()
        if console:
            from rich.progress import Progress, SpinnerColumn, TextColumn
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Loading voice engine...", total=None)
                success = manager.initialize()
                progress.remove_task(task)
        else:
            click.echo("  Loading voice engine...")
            success = manager.initialize()
    else:
        success = manager.initialize()

    if not success:
        print_error(
            "No voice engine available.\n"
            "  Install Chatterbox: pip install chatterbox-tts\n"
            "  Or Coqui TTS:      pip install TTS"
        )
        sys.exit(1)

    if not quiet:
        print_success(f"Engine: {manager.engine_name}")

    return manager


# ═══════════════════════════════════════════════════════════════
# CLI Group
# ═══════════════════════════════════════════════════════════════

@click.group()
@click.version_option(version="0.1.0-dev", prog_name="voiceclone")
@click.option("--verbose", is_flag=True, help="Enable detailed logging")
@click.option("--quiet", is_flag=True, help="Minimal output")
def cli(verbose: bool, quiet: bool) -> None:
    """🎤 VoiceClone — Tu voz. Para siempre.
    
    Voice cloning + personality AI for people with speech disabilities.
    100% local, 100% private — nothing leaves your computer.
    
    \b
    Quick start:
      voiceclone clone myvoice            Clone your voice
      voiceclone speak "Hello" -v myvoice Speak with cloned voice
      voiceclone voices                   List available voices
      voiceclone server                   Start API server
    
    More info: https://github.com/angellocafm-arch/voiceclone
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


# ═══════════════════════════════════════════════════════════════
# Clone Command
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.argument("name")
@click.option(
    "--from", "from_file",
    type=click.Path(exists=True, path_type=Path),
    help="Clone from existing audio file instead of microphone",
)
@click.option(
    "--language", "-l",
    default="es",
    help="Voice language (ISO 639-1 code, default: es)",
)
@click.option("--device", help="Compute device (cuda/mps/cpu)")
@click.option("--quiet", is_flag=True)
def clone(name: str, from_file: Optional[Path], language: str, device: Optional[str], quiet: bool) -> None:
    """Clone a voice from microphone or audio file
    
    \b
    Examples:
      voiceclone clone maria                       Record from mic
      voiceclone clone abuela --from recording.wav Clone from file
      voiceclone clone papa --from video.mp4       Extract voice from video
    
    Reference audio should be 5-30 seconds of clear speech.
    Supported formats: wav, mp3, ogg, m4a, flac, webm
    """
    print_header(f"Clonación de Voz — \"{name}\"")

    if from_file:
        # Clone from file
        print_info(f"Analizando audio: {from_file.name}")
        
        from voice_engine.audio_utils import validate_audio_file
        validation = validate_audio_file(from_file)
        
        if not validation["valid"]:
            for error in validation["errors"]:
                print_error(error)
            sys.exit(1)
        
        if validation["duration_seconds"] > 0:
            print_success(f"Duración: {validation['duration_seconds']:.1f} segundos")
        if validation["sample_rate"] > 0:
            print_success(f"Sample rate: {validation['sample_rate']} Hz")
        for warning in validation.get("warnings", []):
            print_warning(warning)

    else:
        # Record from microphone
        click.echo()
        click.echo("  Vamos a clonar tu voz. Lee el siguiente texto en voz alta:")
        click.echo()
        
        console = get_console()
        if console:
            from rich.panel import Panel
            console.print(Panel(
                '"El sol de la mañana ilumina las calles de la ciudad.\n'
                ' Los pájaros cantan mientras la gente pasea\n'
                ' tranquilamente por el parque. Me gusta este momento\n'
                ' del día, cuando todo está en calma y puedo pensar\n'
                ' con claridad."',
                style="cyan",
            ))
        else:
            click.echo('  "El sol de la mañana ilumina las calles de la ciudad..."')

        click.echo()
        click.confirm("  Pulsa ENTER para empezar a grabar", default=True)
        click.echo("  ● Grabando... (pulsa Ctrl+C para parar)")

        try:
            from voice_engine.audio_utils import record_audio, DEFAULT_SAMPLE_RATE
            import tempfile

            audio_bytes = record_audio(duration_seconds=30.0)
            
            # Save to temp file
            tmp = Path(tempfile.mktemp(suffix=".wav"))
            with open(tmp, "wb") as f:
                f.write(audio_bytes)
            from_file = tmp
            
            print_success("Grabación completada")

        except KeyboardInterrupt:
            click.echo("\n  Grabación detenida")
            # TODO: save partial recording
            sys.exit(0)
        except RuntimeError as e:
            print_error(f"No se pudo grabar: {e}")
            print_info("Usa --from para clonar desde un archivo de audio existente")
            sys.exit(1)

    # Initialize engine and clone
    click.echo()
    manager = get_manager(device=device, quiet=quiet)

    click.echo()
    console = get_console()
    if console:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Procesando voz...", total=None)
            profile = manager.clone_voice(from_file, name)
            progress.remove_task(task)
    else:
        click.echo("  Procesando voz...")
        profile = manager.clone_voice(from_file, name)

    print_success(f'Voz "{profile.name}" clonada correctamente')
    if profile.quality_score is not None:
        quality_label = (
            "Excelente" if profile.quality_score >= 0.8
            else "Buena" if profile.quality_score >= 0.6
            else "Aceptable" if profile.quality_score >= 0.4
            else "Baja"
        )
        print_info(f"Calidad: {quality_label} ({profile.quality_score:.0%})")
    print_info(f"Guardada en: {profile.path}")

    click.echo()
    click.echo("  Usa tu voz con:")
    click.echo(f'    voiceclone speak "tu texto" --voice {profile.name}')


# ═══════════════════════════════════════════════════════════════
# Speak Command
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.argument("text", required=False)
@click.option("--voice", "-v", required=True, help="Voice name to use")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Save to file")
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["wav", "ogg", "mp3"]),
    default="wav",
    help="Output format",
)
@click.option("--exaggeration", "-e", type=float, default=0.5, help="Emotion (0-1)")
@click.option("--cfg", type=float, default=0.5, help="Voice adherence (0-1)")
@click.option("--personality", "-p", is_flag=True, help="Apply personality profile")
@click.option("--device", help="Compute device")
@click.option("--quiet", is_flag=True)
def speak(
    text: Optional[str],
    voice: str,
    output: Optional[Path],
    fmt: str,
    exaggeration: float,
    cfg: float,
    personality: bool,
    device: Optional[str],
    quiet: bool,
) -> None:
    """Synthesize text with a cloned voice
    
    \b
    Examples:
      voiceclone speak "Hola mundo" --voice maria
      voiceclone speak "Hello" -v maria -o output.wav
      echo "Pipe text" | voiceclone speak -v maria
      voiceclone speak "Hola" -v maria --personality
    
    Supports paralinguistic tags: [laugh], [chuckle], [cough]
    """
    # Read from stdin if no text argument
    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print_error("No text provided. Use: voiceclone speak \"your text\" --voice name")
            sys.exit(1)

    if not text:
        print_error("Text cannot be empty")
        sys.exit(1)

    manager = get_manager(device=device, quiet=True)

    # Find voice
    voice_profile = manager.get_voice(voice)
    if voice_profile is None:
        print_error(f'Voice "{voice}" not found')
        available = manager.list_voices()
        if available:
            click.echo("  Available voices:")
            for v in available:
                click.echo(f"    • {v.name}")
        else:
            click.echo("  No voices cloned yet. Use: voiceclone clone <name>")
        sys.exit(1)

    from voice_engine.base import AudioFormat
    format_map = {"wav": AudioFormat.WAV, "ogg": AudioFormat.OGG, "mp3": AudioFormat.MP3}

    if output:
        # Save to file
        if not quiet:
            console = get_console()
            if console:
                from rich.progress import Progress, SpinnerColumn, TextColumn
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Sintetizando...", total=None)
                    result = manager.synthesize(
                        text, voice_profile, format_map[fmt], exaggeration, cfg
                    )
                    progress.remove_task(task)
            else:
                result = manager.synthesize(
                    text, voice_profile, format_map[fmt], exaggeration, cfg
                )
        else:
            result = manager.synthesize(
                text, voice_profile, format_map[fmt], exaggeration, cfg
            )

        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "wb") as f:
            f.write(result.audio_data)

        if not quiet:
            print_success(
                f"Audio guardado: {output} "
                f"({result.duration_seconds:.1f}s, {len(result.audio_data) // 1024}KB)"
            )
    else:
        # Play audio
        if not quiet:
            click.echo(f'\n  🔊 Reproduciendo: "{text[:50]}..."' if len(text) > 50 else f'\n  🔊 Reproduciendo: "{text}"')

        result = manager.synthesize(
            text, voice_profile, AudioFormat.WAV, exaggeration, cfg
        )

        # Try to play audio
        try:
            import numpy as np
            import sounddevice as sd

            audio = np.frombuffer(result.audio_data, dtype=np.float32)
            sd.play(audio, result.sample_rate)
            sd.wait()
        except ImportError:
            # Fallback: save to temp and play with system player
            import tempfile
            import subprocess

            tmp = Path(tempfile.mktemp(suffix=".wav"))
            with open(tmp, "wb") as f:
                f.write(result.audio_data)

            try:
                if sys.platform == "darwin":
                    subprocess.run(["afplay", str(tmp)], check=True)
                elif sys.platform == "linux":
                    subprocess.run(["aplay", str(tmp)], check=True)
                elif sys.platform == "win32":
                    import os
                    os.startfile(str(tmp))
            except Exception:
                print_warning(f"Could not play audio. Saved to: {tmp}")
            finally:
                try:
                    tmp.unlink()
                except Exception:
                    pass

        if not quiet:
            print_info(f"  ▶ {result.duration_seconds:.1f}s")


# ═══════════════════════════════════════════════════════════════
# Voices Command
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.option("--device", help="Compute device")
def voices(device: Optional[str]) -> None:
    """List all cloned voices
    
    Shows name, creation date, engine, and personality status.
    """
    print_header("Voces Disponibles")

    manager = get_manager(device=device, quiet=True)
    voice_list = manager.list_voices()

    if not voice_list:
        click.echo("  No hay voces clonadas todavía.\n")
        click.echo("  Empieza con:")
        click.echo("    voiceclone clone <nombre>")
        return

    console = get_console()
    if console:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Nombre", style="bold")
        table.add_column("Creada")
        table.add_column("Personalidad")
        table.add_column("Motor")
        table.add_column("Calidad")

        for v in voice_list:
            date_str = v.created_at[:10] if v.created_at else "—"
            personality = "✅ Activada" if v.has_personality else "❌ No"
            engine = v.engine or "—"
            quality = f"{v.quality_score:.0%}" if v.quality_score else "—"

            table.add_row(v.name, date_str, personality, engine, quality)

        console.print(table)
    else:
        click.echo(f"  {'NOMBRE':<15} {'CREADA':<12} {'PERSONALIDAD':<15} {'MOTOR':<12}")
        click.echo(f"  {'─'*15} {'─'*12} {'─'*15} {'─'*12}")
        for v in voice_list:
            date_str = v.created_at[:10] if v.created_at else "—"
            personality = "✅" if v.has_personality else "❌"
            click.echo(f"  {v.name:<15} {date_str:<12} {personality:<15} {v.engine:<12}")

    click.echo(f"\n  {len(voice_list)} voces · Motor activo: {manager.engine_name}")


# ═══════════════════════════════════════════════════════════════
# Voices Delete Command
# ═══════════════════════════════════════════════════════════════

@cli.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--device", help="Compute device")
def delete_voice(name: str, yes: bool, device: Optional[str]) -> None:
    """Delete a cloned voice
    
    Removes the voice, its reference audio, personality profile,
    and all generated samples. THIS CANNOT BE UNDONE.
    """
    manager = get_manager(device=device, quiet=True)

    voice = manager.get_voice(name)
    if voice is None:
        print_error(f'Voice "{name}" not found')
        sys.exit(1)

    if not yes:
        click.echo(f'\n  ⚠️  ¿Eliminar la voz "{name}" y todos sus datos?')
        click.echo("  Esto incluye: audio original, embedding, personalidad.")
        click.echo("  Esta acción NO se puede deshacer.\n")
        confirm = click.prompt(f'  Escribe "{name}" para confirmar')
        if confirm != name:
            click.echo("  Cancelado.")
            return

    if manager.delete_voice(name):
        print_success(f'Voz "{name}" eliminada')
    else:
        print_error(f'Error al eliminar "{name}"')


# ═══════════════════════════════════════════════════════════════
# Server Command
# ═══════════════════════════════════════════════════════════════

@cli.command()
@click.option("--host", default="127.0.0.1", help="Bind address (default: localhost)")
@click.option("--port", "-p", default=8765, help="Port (default: 8765)")
@click.option("--device", help="Compute device")
def server(host: str, port: int, device: Optional[str]) -> None:
    """Start the VoiceClone API server
    
    Runs a local FastAPI server at http://localhost:8765
    
    \b
    Endpoints:
      POST /clone     Clone voice from audio
      POST /speak     Synthesize text
      GET  /voices    List voices
      GET  /health    Server status
    
    The server only listens on localhost — never exposed to the network.
    """
    print_header("VoiceClone API Server")

    # Pre-initialize engine
    manager = get_manager(device=device)

    print_success(f"Motor: {manager.engine_name}")
    print_success(f"Voces cargadas: {len(manager.list_voices())}")
    print_success(f"API: http://{host}:{port}")
    
    click.echo()
    click.echo("  Endpoints:")
    click.echo("    POST /clone        Clonar voz")
    click.echo("    POST /speak        Sintetizar texto")
    click.echo("    GET  /voices       Listar voces")
    click.echo("    GET  /health       Estado del servicio")
    click.echo()
    click.echo("  Ctrl+C para parar")
    click.echo()

    try:
        import uvicorn
        # Import here to avoid circular imports
        # The server module will be created in Task 3.4
        uvicorn.run(
            "api.server:app",
            host=host,
            port=port,
            log_level="info",
            reload=False,
        )
    except ImportError:
        print_error("uvicorn not installed. Install with: pip install uvicorn[standard]")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n  Server detenido.")


# ═══════════════════════════════════════════════════════════════
# Config Command
# ═══════════════════════════════════════════════════════════════

@cli.command()
def config() -> None:
    """Show VoiceClone configuration
    
    Displays storage paths, active engine, and system info.
    """
    import platform
    
    print_header("Configuración de VoiceClone")

    click.echo(f"  Directorio: {DEFAULT_DIR}")
    click.echo(f"  Voces: {DEFAULT_DIR / 'voices'}")
    click.echo(f"  Modelos: {DEFAULT_DIR / 'models'}")
    click.echo()
    click.echo(f"  Sistema: {platform.system()} {platform.machine()}")
    click.echo(f"  Python: {platform.python_version()}")

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            click.echo(f"  GPU: CUDA ({torch.cuda.get_device_name(0)})")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            click.echo("  GPU: Apple Silicon (MPS)")
        else:
            click.echo("  GPU: No (using CPU)")
    except ImportError:
        click.echo("  GPU: PyTorch not installed")

    # Check engines
    click.echo()
    try:
        import chatterbox
        click.echo("  ✅ Chatterbox TTS installed")
    except ImportError:
        click.echo("  ❌ Chatterbox TTS not installed")

    try:
        import TTS
        click.echo("  ✅ Coqui TTS (XTTS v2) installed")
    except ImportError:
        click.echo("  ❌ Coqui TTS not installed")


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

def main():
    """Entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()
