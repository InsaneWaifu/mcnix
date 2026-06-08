import json
import urllib.request
import urllib.parse
import hashlib
import base64
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
USER_AGENT = "NixPluginFetcher/1.0 (Helper script for Nix expressions)"


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        console.print(
            f"\n[bold red][-] Error fetching data from API:[/bold red] {e}"
        )
        sys.exit(1)


def compute_nix_sri_hash(download_url):
    req = urllib.request.Request(
        download_url, headers={"User-Agent": USER_AGENT}
    )
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task(
                description="Downloading plugin to calculate Nix hash...",
                total=None,
            )
            with urllib.request.urlopen(req) as response:
                file_data = response.read()
                sha256_digest = hashlib.sha256(file_data).digest()
                return f"sha256-{base64.b64encode(sha256_digest).decode()}"
    except Exception as e:
        console.print(
            "[bold red][-] Failed to download asset for hashing:[/bold red]"
            f" {e}"
        )
        return "sha256-HASH_FAILED_PLACEHOLDER="


def handle_hangar():
    query = Prompt.ask("\n[bold cyan]Enter Hangar search query[/bold cyan]")
    if not query:
        return

    url = (
        "https://hangar.papermc.io/api/v1/projects?q="
        f"{urllib.parse.quote(query)}&limit=10"
    )
    data = request_json(url)
    results = data.get("result", [])

    if not results:
        console.print("[yellow]No plugins found on Hangar.[/yellow]")
        return

    table = Table(title="Found Hangar Plugins", title_style="bold magenta")
    table.add_column("Num", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Slug", style="bold yellow")
    table.add_column("Description", style="white")

    for idx, project in enumerate(results):
        table.add_row(
            str(idx + 1),
            project["name"],
            project["namespace"]["slug"],
            f"{project['description'][:60]}...",
        )
    console.print(table)

    choice = (
        IntPrompt.ask(
            "[bold cyan]Select a plugin number[/bold cyan]",
            choices=[str(i + 1) for i in range(len(results))],
        )
        - 1
    )
    selected = results[choice]
    slug = selected["namespace"]["slug"]

    v_url = (
        f"https://hangar.papermc.io/api/v1/projects/{slug}/versions?limit=10"
    )
    v_data = request_json(v_url)
    versions = v_data.get("result", [])

    v_table = Table(
        title=f"Recent Versions for {selected['name']}",
        title_style="bold magenta",
    )
    v_table.add_column("Num", justify="right", style="cyan", no_wrap=True)
    v_table.add_column("Version", style="green")
    v_table.add_column("Platforms", style="yellow")

    for idx, v in enumerate(versions):
        platforms = ", ".join(v.get("platforms", {}).keys())
        v_table.add_row(str(idx + 1), v["name"], platforms)
    console.print(v_table)

    v_choice = (
        IntPrompt.ask(
            "[bold cyan]Select a version number[/bold cyan]",
            choices=[str(i + 1) for i in range(len(versions))],
        )
        - 1
    )
    selected_version = versions[v_choice]["name"]

    dl_url = (
        "https://hangar.papermc.io/api/v1/projects"
        f"/{slug}/versions/{selected_version}/PAPER/download"
    )
    nix_hash = compute_nix_sri_hash(dl_url)

    console.print(
        Panel(
            "[bold green]Generated Nix Expression Output[/bold green]",
            expand=False,
        )
    )
    print(f'(fetchHangarPlugin "{slug}" "{selected_version}" "{nix_hash}")')


def handle_spigot():
    query = Prompt.ask("\n[bold cyan]Enter Spigot search query[/bold cyan]")
    if not query:
        return

    url = (
        "https://api.spiget.org/v2/search/resources/"
        f"{urllib.parse.quote(query)}?size=10&fields=id,name,tag"
    )
    results = request_json(url)

    if not results:
        console.print("[yellow]No plugins found on Spigot.[/yellow]")
        return

    table = Table(title="Found Spigot Plugins", title_style="bold magenta")
    table.add_column("Num", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="bold yellow")
    table.add_column("Tagline", style="white")

    for idx, project in enumerate(results):
        table.add_row(
            str(idx + 1),
            project["name"],
            str(project["id"]),
            f"{project.get('tag', '')[:60]}...",
        )
    console.print(table)

    choice = (
        IntPrompt.ask(
            "[bold cyan]Select a plugin number[/bold cyan]",
            choices=[str(i + 1) for i in range(len(results))],
        )
        - 1
    )
    selected = results[choice]
    plugin_id = selected["id"]
    plugin_name = selected["name"].replace(" ", "-").lower()

    v_url = (
        "https://api.spiget.org/v2/resources/"
        f"{plugin_id}/versions?size=10&sort=-releaseDate"
    )

    versions = request_json(v_url)

    v_table = Table(
        title=f"Recent Versions for {selected['name']}",
        title_style="bold magenta",
    )
    v_table.add_column("Num", justify="right", style="cyan", no_wrap=True)
    v_table.add_column("Version Name", style="green")
    v_table.add_column("Version ID", style="yellow")

    for idx, v in enumerate(versions):
        v_table.add_row(str(idx + 1), v["name"], str(v["id"]))
    console.print(v_table)

    v_choice = (
        IntPrompt.ask(
            "[bold cyan]Select a version number[/bold cyan]",
            choices=[str(i + 1) for i in range(len(versions))],
        )
        - 1
    )
    selected_version_id = versions[v_choice]["id"]

    dl_url = (
        "https://api.spiget.org/v2/resources/"
        f"{plugin_id}/versions/{selected_version_id}/download/proxy"
    )

    nix_hash = compute_nix_sri_hash(dl_url)

    console.print(
        Panel(
            "[bold green]Generated Nix Expression Output[/bold green]",
            expand=False,
        )
    )
    print(
        "(fetchSpigotPlugin "
        + f'"{plugin_name}" "{plugin_id}"'
        + f'"{selected_version_id}" "{nix_hash}")'
    )


def main():
    while True:
        console.print(
            Panel.fit(
                "[bold violet]Minecraft Plugin Nix Fetcher[/bold violet]",
                border_style="violet",
            )
        )
        console.print(
            "[bold dim]1.[/bold dim] [cyan]Search PaperMC Hangar[/cyan]"
        )
        console.print(
            "[bold dim]2.[/bold dim] [cyan]Search SpigotMC (Spiget)[/cyan]"
        )
        console.print("[bold dim]3.[/bold dim] [red]Exit[/red]")
        choice = Prompt.ask(
            "\n[bold white]Choose platform[/bold white]",
            choices=["1", "2", "3"],
        )

        if choice == "1":
            handle_hangar()
        elif choice == "2":
            handle_spigot()
        elif choice == "3":
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break
        console.print("\n")


if __name__ == "__main__":
    main()
