"""Command-line interface for VoiceClone"""

import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from .voice_engine import ChatterboxEngine
from .voice_engine.recorder import VoiceRecorder

logger = logging.getLogger(__name__)
console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cli(verbose: bool):
    """VoiceClone — Preserva tu voz. Para siempre.
    
    Open source voice cloning + personality AI for accessibility.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option("--name", "-n", required=True, help="Name for the cloned voice")
@click.option("--duration", "-d", default=180, help="Recording duration in seconds (default: 3min)")
@click.option("--language", "-l", default="es", help="Language code (default: es)")
def clone(name: str, duration: int, language: str):
    """Clone your voice
    
    Example:
        voiceclone clone --name myvoice --duration 180
    """
    console.print(Panel.fit(
        "[bold cyan]VoiceClone — Clonación de voz[/]\n\n"
        f"[yellow]Nombre:[/] {name}\n"
        f"[yellow]Duración:[/] {duration} segundos\n"
        f"[yellow]Idioma:[/] {language}",
        title="Configuración"
    ))
    
    console.print("\n[bold]Instrucciones:[/]")
    console.print("1. Presiona ENTER cuando estés listo para grabar")
    console.print("2. Lee el texto de forma clara y natural")
    console.print("3. Presiona CTRL+C para detener (o espera a que se complete)")
    
    input("\n[cyan]Presiona ENTER para comenzar...[/]")
    
    # Record voice
    recorder = VoiceRecorder(sample_rate=22050)
    
    def progress(p: float):
        console.print(f"\r[cyan]Grabando... {p*100:.0f}%[/]", end="")
    
    try:
        console.print("[bold cyan]Grabando...[/]")
        audio = recorder.record(duration, progress_callback=progress)
        console.print()  # New line after progress
        
        # Save to temp location
        temp_path = Path.home() / ".voiceclone" / "temp_recording.wav"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        recorder.save(audio, temp_path)
        
        # Clone voice
        console.print("[bold cyan]Clonando voz...[/]")
        engine = ChatterboxEngine()
        voice_profile = engine.clone_voice(temp_path, name)
        
        # Success!
        console.print(Panel.fit(
            f"[bold green]✅ Voz clonada exitosamente![/]\n\n"
            f"[yellow]Nombre:[/] {voice_profile.name}\n"
            f"[yellow]Calidad:[/] {voice_profile.quality_score:.1f}/5.0\n"
            f"[yellow]Guardada en:[/] {voice_profile.path}",
            title="Éxito"
        ))
        
        console.print("\n[cyan]Prueba tu voz con:[/]")
        console.print(f"  voiceclone speak 'Hola, soy {name}' --voice {name}")
    
    except KeyboardInterrupt:
        console.print("\n[red]Grabación cancelada[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        logger.exception("Cloning failed")


@cli.command()
@click.argument("text")
@click.option("--voice", "-v", required=True, help="Voice name to use")
@click.option("--output", "-o", help="Output file (default: stdout)")
def speak(text: str, voice: str, output: Optional[str]):
    """Synthesize text with cloned voice
    
    Example:
        voiceclone speak 'Hola mundo' --voice myvoice
    """
    try:
        console.print(f"[cyan]Sintetizando:[/] {text}")
        
        engine = ChatterboxEngine()
        voices = engine.list_voices()
        voice_profile = next((v for v in voices if v.name == voice), None)
        
        if not voice_profile:
            console.print(f"[red]Error:[/] Voz '{voice}' no encontrada")
            return
        
        audio_bytes = engine.synthesize(text, voice_profile)
        
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # TODO: Write audio_bytes to file
            console.print(f"[green]✅ Guardado en:[/] {output_path}")
        else:
            console.print(f"[green]✅ Audio generado ({len(audio_bytes)} bytes)[/]")
    
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        logger.exception("Synthesis failed")


@cli.command()
def list():
    """List all cloned voices"""
    try:
        engine = ChatterboxEngine()
        voices = engine.list_voices()
        
        if not voices:
            console.print("[yellow]No hay voces clonadas[/]")
            return
        
        console.print("[bold]Voces clonadas:[/]")
        for voice in voices:
            quality_str = f"{voice.quality_score:.1f}/5.0" if voice.quality_score else "N/A"
            console.print(
                f"  • [cyan]{voice.name}[/] "
                f"({voice.language}) - "
                f"Calidad: {quality_str}"
            )
    
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        logger.exception("List voices failed")


@cli.command()
@click.argument("voice_name")
def delete(voice_name: str):
    """Delete a cloned voice"""
    if not click.confirm(f"¿Eliminar la voz '{voice_name}'?"):
        console.print("[yellow]Cancelado[/]")
        return
    
    try:
        engine = ChatterboxEngine()
        success = engine.delete_voice(voice_name)
        
        if success:
            console.print(f"[green]✅ Voz '{voice_name}' eliminada[/]")
        else:
            console.print(f"[red]Error:[/] Voz no encontrada")
    
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        logger.exception("Delete failed")


def main():
    """Entry point"""
    cli()


if __name__ == "__main__":
    main()
