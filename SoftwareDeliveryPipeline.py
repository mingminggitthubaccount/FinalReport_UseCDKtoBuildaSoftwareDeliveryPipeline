from aws_cdk import (
    core,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_iam as iam,
)

class SoftwareDeliveryPipelineStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 Bucket for artifacts
        artifact_bucket = s3.Bucket(self, "ArtifactBucket")

        # CodeCommit Repository
        code_repo = codecommit.Repository(
            self, "JavaProjectRepo",
            repository_name="java-project",
            code=codecommit.Code.from_asset("finalProject/SoftwareDeliveryPipeline/java-project.zip")
        )

        # CodeBuild Project
        build_project = codebuild.Project(
            self, "JavaBuildProject",
            source=codebuild.Source.code_commit(repository=code_repo),
            build_spec=codebuild.BuildSpec.from_source_filename('buildspec.yml'),
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_5_0),
            artifacts=codebuild.Artifacts.s3(
                bucket=artifact_bucket,
                include_build_id=True,
                package_zip=True
            ),
        )

        # IAM Role for CodePipeline
        pipeline_role = iam.Role(
            self, "CodePipelineServiceRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ]
        )

        # CodePipeline
        pipeline = codepipeline.Pipeline(
            self, "DeliveryPipeline",
            pipeline_name="JavaProjectPipeline",
            artifact_bucket=artifact_bucket,
            role=pipeline_role,
        )

        # Add stages to pipeline
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        pipeline.add_stage(
            stage_name="Source",
            actions=[codepipeline_actions.CodeCommitSourceAction(
                action_name="CodeCommit",
                repository=code_repo,
                output=source_output,
            )]
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[codepipeline_actions.CodeBuildAction(
                action_name="CodeBuild",
                project=build_project,
                input=source_output,
                outputs=[build_output],
            )]
        )

app = core.App()
SoftwareDeliveryPipelineStack(app, "SoftwareDeliveryPipelineStack")
app.synth()
