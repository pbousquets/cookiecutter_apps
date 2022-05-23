__author__ = "{{cookiecutter.author_name}}"
__year__ = "{{cookiecutter.year}}"


from os.path import join
from shutil import which

from isabl_cli import AbstractApplication
from isabl_cli import options

from .constants import application_results
import click


class {{cookiecutter.app_name}}(AbstractApplication):

    """{{cookiecutter.description}}"""

    # The uniqueness of an application is determined by it's name and version
    # A good strategy to versioning apps is to ask: are results still comparable?
    # An optimization that doesn't change outputs might not require a version change.
    NAME = "{{cookiecutter.app_full_name}}"
    VERSION = "{{cookiecutter.version}}"

    # Optionally set ASSEMBLY and SPECIES to version as a function of genome build.
    # This is particularly useful for NGS applications as often results are only
    # comparable if data was analyzed against the same version of the genome.
    ASSEMBLY =  {%- if cookiecutter.assembly == "None" -%}  None {%- elif cookiecutter.assembly != "None" -%} "{{cookiecutter.assembly}}" {% endif %}
    SPECIES = "{{cookiecutter.species.upper()}}"

    # You can add additional metadata to be attached to the database object
    # URL (or comma separated URLs) to be stored in the application database object.
    application_description = "{{cookiecutter.description}}"
    application_url = "https://docs.isabl.io/writing-applications"

    # Applications can depend on multiple configurations such as paths to executables,
    # references files, compute requirements, etc. These settings are explicitly
    # defined using the application_settings dictionary. Learn more at:
    # https://docs.isabl.io/writing-applications#application-settings
    application_import_strings = {"sym_link"}
    application_settings = {
        "echo_path": "echo",
        "default_message": "Hello World",
        "sym_link": "isabl_cli.utils.force_symlink",
    }

    # Applications can be launched from the command line. To support this capability
    # you have to tell the application how to link analyses to different experiments.
    # Learn more: https://docs.isabl.io/writing-applications#command-line-configuration
    cli_help = "{{cookiecutter.description}}"
    cli_options = [options.TARGETS, click.option("--message")]
    cli_allow_force = True
    cli_allow_restart = True
    cli_allow_local = True

    # You can provide an specification your application results using this attribute.
    # Each key is a result id and the value is a dictionary with specs of the result.
    # By default, analysis results are protected upon completion (i.e. permissions are
    # set to read only). Disabling application_protect_results makes an app re-runnable.
    application_protect_results = False
    
    # Isabl applications can produce auto-merge analyses at a project and individual
    # level. For example, you may want to merge variants whenever new results are
    # available for a given project, or update quality control reports when a new
    # sample is added to an individual.
    application_project_level_results = {
        "merged": {
            "frontend_type": "text-file",
            "description": "Merged output files.",
            "verbose_name": "Merged Output Files",
        },
        "count": {
            "frontend_type": "number",
            "description": "Count of characters for merged output.",
            "verbose_name": "Merged Output Characters Count",
        },
    }

    # application_inputs are analysis-specific settings (settings are the same for all
    # analyses, yet inputs are potentially different for each analysis). Each input set
    # to NotImplemented is considered required and must be resolved at get_dependencies.
    # This mechanism enables you to link new analysis to previous ones. You can learn
    # more at: https://docs.isabl.io/writing-applications#application-settings
    application_inputs = dict()

    # You can make sure applications are properly configured by validating settings.
    # To do so, simply raise an AssertionError if something is not set properly.
    def validate_settings(self, settings):
        assert which(settings.echo_path), f"{settings.echo_path} not in PATH"

    # Some of the advantages of metadata-driven applications is that we can prevent
    # analyses that don't make sense, for example running a variant calling application
    # on imaging data. Simply raise an AssertionError if something doesn't make sense,
    # and the error message will be provided to the user.
    def validate_experiments(self, targets, references):
        assert len(targets) == 1, "only one target experiment per analysis"
        assert targets[0].raw_data, "target experiment has no linked raw data"

    # Lets dive into creating data processing commands. Note that Isabl is agnostic to
    # compute architecture, therefore our only objective is to build the shell command
    # that will run the analysis and return it as a string.
    def get_command(self, analysis, inputs, settings):
        echo = settings.echo_path
        target = analysis.targets[0]
        output_file = join(analysis.storage_url, "output.txt")
        input_file = join(analysis.storage_url, "input.txt")
        message = settings.run_args.get("message") or settings.default_message
        settings.sym_link(target.raw_data[0].file_url, input_file)
        return (
            f"bash -c '{echo} Sample: {target.sample.identifier} > {output_file}' && "
            f"bash -c '{echo} Message: {message} >> {output_file}' && "
            f"bash -c '{echo} Data: >> {output_file}' && "
            f"bash -c 'zcat {input_file} |wc -l >> {output_file}' "
        )

    # When application_results is defined, you must implement get_analysis_results.
    # This method is only run after the analysis has been run successfully.
    def get_analysis_results(self, analysis):
        output = join(analysis.storage_url, "output.txt")

        with open(output) as f:
            count = sum(len(i) for i in f)

        return {
            "input": join(analysis.storage_url, "input.txt"),
            "output": output,
            "count": count,
        }

    # A newly versioned analysis will be created for each type of auto-merge.
    # Your role is to take a list of succeeded analysis and implement the merge logic.
    def merge_project_analyses(self, analysis, analyses):
        with open(join(analysis.storage_url, "merged.txt"), "w") as f:
            for i in analyses:
                with open(i.results.output) as output:
                    f.write(output.read())

    # Just as regular analyses, we have to provide logic to build the results
    # dictionary for the individual / project level analyses.
    def get_project_analysis_results(self, analysis):
        merged = join(analysis.storage_url, "merged.txt")

        with open(merged) as f:
            count = sum(len(i) for i in f)

        return {"merged": merged, "count": count}

    # Here we'll just recycle the project level merge logic for individual level merge
    application_individual_level_results = application_project_level_results
    merge_individual_analyses = merge_project_analyses
    get_individual_analysis_results = get_project_analysis_results


