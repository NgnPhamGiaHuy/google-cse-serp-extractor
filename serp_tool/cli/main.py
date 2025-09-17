import asyncio
import sys
import click
from pathlib import Path
from typing import Optional

from models import SearchConfig
from serp_tool.scraper import GoogleSerpScraper
from serp_tool.handlers.writers import export_results
from serp_tool.utils.temp_manager import get_inspections_dir, cleanup_temp_dir
from config import config as app_config
from serp_tool.logging import cli_logger, setup_root_logging

from .helpers import load_keywords, build_config_from_flags, deduplicate_and_log
from serp_tool.utils.usage_tracker import UsageTracker, DailyQuotaExceededError


# Root command group
@click.group()
def main():
    """SERP Tool CLI"""
    pass


# Existing scrape command preserved as a subcommand
@main.command("scrape")
@click.option('--keywords', '-k', required=True, help='Path to keywords file (JSON, CSV, or Excel)')
@click.option('--output', '-o', required=True, help='Output file path (JSON, CSV, or Excel)')
@click.option('--max-pages', '-p', default=None, type=click.IntRange(1), help='Maximum pages to scrape (default from config)')
@click.option('--include-organic/--no-organic', default=True, help='Include organic results (default: True)')
@click.option('--include-paa/--no-paa', default=False, help='Include People Also Ask (default: False)')
@click.option('--include-related/--no-related', default=False, help='Include related searches (default: False)')
@click.option('--include-ads/--no-ads', default=False, help='Include ads (default: False)')
@click.option('--include-ai-overview/--no-ai-overview', default=False, help='Include AI overview (default: False)')
@click.option('--profile-site', multiple=True, help='Add profile site filter(s), e.g., --profile-site site:github.com. Defaults to LinkedIn only if none provided.')
@click.option('--allow-duplicates/--no-allow-duplicates', default=False, help='Allow duplicate queries after normalization (default: no-allow-duplicates)')
def scrape(
    keywords: str,
    output: str,
    max_pages: int,
    include_organic: bool,
    include_paa: bool,
    include_related: bool,
    include_ads: bool,
    include_ai_overview: bool,
    profile_site: Optional[list],
    allow_duplicates: bool
):

    async def run_scraping():
        try:
            keywords_path = Path(keywords)
            if not keywords_path.exists():
                click.echo(f"Error: Keywords file not found: {keywords}", err=True)
                return

            click.echo(f"Reading keywords from {keywords}...")
            try:
                keyword_list = load_keywords(keywords_path)
                click.echo(f"Found {len(keyword_list)} keywords")
            except Exception as e:
                click.echo(f"Error reading keywords file: {str(e)}", err=True)
                return

            if not keyword_list:
                click.echo("No keywords found in the file", err=True)
                return

            default_profile_sites = [
                'site:vn.linkedin.com/in'
            ]
            selected_sites = list(profile_site) if profile_site else default_profile_sites
            defaults = app_config.search_defaults if hasattr(app_config, 'search_defaults') else {}
            config = build_config_from_flags(
                SearchConfig,
                defaults,
                include_organic,
                include_paa,
                include_related,
                include_ads,
                include_ai_overview,
                selected_sites,
                allow_duplicates,
                max_pages,
                None,
            )

            click.echo("\nScraping Configuration:")
            click.echo(f"  Max Pages: {config.max_pages}")
            click.echo(f"  Results per Page: {config.results_per_page}")

            result_types = []
            if config.include_organic:
                result_types.append("organic")
            if config.include_paa:
                result_types.append("PAA")
            if config.include_related:
                result_types.append("related")
            if config.include_ads:
                result_types.append("ads")
            if config.include_ai_overview:
                result_types.append("AI overview")
            click.echo(f"  Result Types: {', '.join(result_types)}")
            click.echo()

            try:
                scraper = GoogleSerpScraper()
            except ValueError as e:
                click.echo(f"Error: {str(e)}", err=True)
                click.echo("\n💡 Quick fix options:", err=True)
                click.echo("1. Create a .env file with: GOOGLE_API_KEY=your_key_here and GOOGLE_CSE_CX=your_cx_here", err=True)
                click.echo("2. Set environment variables: export GOOGLE_API_KEY=your_key_here and export GOOGLE_CSE_CX=your_cx_here", err=True)
                return

            cli_logger.info("Starting scraping process", extra={"action": "start", "status": "success"})

            insp_dir = get_inspections_dir()
            log_path = insp_dir / 'queries.log'
            unique_keywords, skipped_duplicates = deduplicate_and_log(keyword_list, config, log_path)

            cli_logger.info(
                f"Sending {len(unique_keywords)} unique querie(s) to Google CSE",
                extra={"action": "cse_batch", "status": "started"}
            )
            all_results = []
            with click.progressbar(unique_keywords, label='Scraping keywords') as keywords_bar:
                for keyword in keywords_bar:
                    try:
                        results = await scraper.scrape_keyword(keyword, config)
                        all_results.extend(results)
                        cli_logger.info(
                            f"{keyword}: {len(results)} results",
                            extra={"action": "result_fetch", "status": "success", "keyword": keyword}
                        )
                    except DailyQuotaExceededError as e:
                        msg = str(e)
                        cli_logger.error(msg, extra={"action": "daily_quota", "status": "fail"})
                        click.echo(f"Error: {msg}", err=True)
                        raise SystemExit(1)
                    except Exception as e:
                        cli_logger.error(
                            f"Error scraping '{keyword}': {str(e)}",
                            extra={"action": "scrape", "status": "fail", "keyword": keyword}
                        )
                    await asyncio.sleep(1)

            try:
                from serp_tool.handlers.flatteners import _flatten_organic
                organic_rows_count = len(_flatten_organic(all_results))
            except Exception:
                organic_rows_count = 0
            cli_logger.info(
                f"Scraping completed: sent={len(unique_keywords)}, cse_items={len(all_results)}, organic_rows={organic_rows_count}",
                extra={"action": "complete", "status": "success"}
            )

            cli_logger.info(f"Exporting results to {output}", extra={"action": "export", "status": "started"})
            try:
                export_results(all_results, output)
                cli_logger.info("Export success", extra={"action": "export", "status": "success"})
            except Exception as e:
                cli_logger.error(f"Export failed: {str(e)}", extra={"action": "export", "status": "fail"})
                return

            click.echo("\n=== Summary ===")
            click.echo(f"Keywords processed: {len(keyword_list)}")
            click.echo(f"Total results: {len(all_results)}")

            result_types_count = {}
            for result in all_results:
                result_type = result.type
                result_types_count[result_type] = result_types_count.get(result_type, 0) + 1
            for result_type, count in result_types_count.items():
                click.echo(f"  {result_type}: {count}")
            click.echo(f"Output file: {output}")

        except KeyboardInterrupt:
            cli_logger.error("Scraping interrupted by user", extra={"action": "interrupt", "status": "fail"})
        except Exception as e:
            cli_logger.error(f"Unexpected error: {str(e)}", extra={"action": "unexpected", "status": "fail"})
        finally:
            cleanup_temp_dir()

    setup_root_logging()
    asyncio.run(run_scraping())


@main.command("usage")
def usage() -> None:
    """Print today's API request usage summary."""
    setup_root_logging()
    tracker = UsageTracker.get_shared()
    snap = tracker.get_snapshot()
    click.echo(f"Requests used today: {snap.used} / {snap.quota}")
    if snap.used >= snap.quota:
        click.echo("Daily request limit reached. Please try again tomorrow.", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

