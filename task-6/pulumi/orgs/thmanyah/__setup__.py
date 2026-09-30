import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config("stream")


def create_bucket(env):
    _bucket = aws.s3.Bucket(
        f"recordings-{env}",
        bucket_prefix=config.get("bucket_prefix"),
        force_destroy=True,
    )
    return _bucket


def create_role(env, bucket):
    _role = aws.iam.Role(
        f"medialive-{env}",
        assume_role_policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "medialive.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )

    aws.iam.RolePolicy(
        f"medialive-{env}",
        role=_role.id,
        policy=bucket.arn.apply(
            lambda arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
                            "Resource": arn,
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
                            "Resource": f"{arn}/*",
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogStreams",
                                "logs:DescribeLogGroups",
                            ],
                            "Resource": "*",
                        },
                    ],
                }
            )
        ),
    )
    return _role


def create_input(env):
    # Only the source address may push to the input
    _security_group = aws.medialive.InputSecurityGroup(
        f"obs-{env}",
        whitelist_rules=[
            aws.medialive.InputSecurityGroupWhitelistRuleArgs(cidr=config.get("source_cidr"))
        ],
    )

    _input = aws.medialive.Input(
        f"obs-{env}",
        name=f"obs-{env}",
        type="RTP_PUSH",
        input_security_groups=[_security_group.id],
    )
    return _input


def create_channel(env, input, role, bucket):
    _channel = aws.medialive.Channel(
        f"obs-{env}",
        name=f"obs-{env}",
        channel_class="SINGLE_PIPELINE",
        role_arn=role.arn,
        log_level="INFO",
        input_specification=aws.medialive.ChannelInputSpecificationArgs(
            codec="HEVC",
            input_resolution="HD",
            maximum_bitrate="MAX_20_MBPS",
        ),
        input_attachments=[
            aws.medialive.ChannelInputAttachmentArgs(
                input_attachment_name="obs",
                input_id=input.id,
                input_settings=aws.medialive.ChannelInputAttachmentInputSettingsArgs(
                    audio_selectors=[
                        aws.medialive.ChannelInputAttachmentInputSettingsAudioSelectorArgs(
                            name="default"
                        )
                    ],
                ),
            )
        ],
        destinations=[
            aws.medialive.ChannelDestinationArgs(
                id="recordings",
                settings=[
                    aws.medialive.ChannelDestinationSettingArgs(
                        url=bucket.bucket.apply(
                            lambda name: f"s3ssl://{name}/{config.get('recording_path')}"
                        )
                    )
                ],
            )
        ],
        encoder_settings=aws.medialive.ChannelEncoderSettingsArgs(
            timecode_config=aws.medialive.ChannelEncoderSettingsTimecodeConfigArgs(
                source="SYSTEMCLOCK"
            ),
            audio_descriptions=[
                aws.medialive.ChannelEncoderSettingsAudioDescriptionArgs(
                    name="audio",
                    audio_selector_name="default",
                    codec_settings=aws.medialive.ChannelEncoderSettingsAudioDescriptionCodecSettingsArgs(
                        aac_settings=aws.medialive.ChannelEncoderSettingsAudioDescriptionCodecSettingsAacSettingsArgs(
                            bitrate=config.get_int("audio_bitrate"),
                            coding_mode="CODING_MODE_2_0",
                            sample_rate=48000,
                            rate_control_mode="CBR",
                            profile="LC",
                            spec="MPEG4",
                            input_type="NORMAL",
                        )
                    ),
                )
            ],
            video_descriptions=[
                aws.medialive.ChannelEncoderSettingsVideoDescriptionArgs(
                    name="video",
                    width=config.get_int("video_width"),
                    height=config.get_int("video_height"),
                    codec_settings=aws.medialive.ChannelEncoderSettingsVideoDescriptionCodecSettingsArgs(
                        h265_settings=aws.medialive.ChannelEncoderSettingsVideoDescriptionCodecSettingsH265SettingsArgs(
                            bitrate=config.get_int("video_bitrate"),
                            rate_control_mode="CBR",
                            framerate_numerator=config.get_int("video_framerate"),
                            framerate_denominator=1,
                            profile="MAIN",
                            level="H265_LEVEL_AUTO",
                            gop_size=2,
                            gop_size_units="SECONDS",
                            scan_type="PROGRESSIVE",
                        )
                    ),
                )
            ],
            output_groups=[
                aws.medialive.ChannelEncoderSettingsOutputGroupArgs(
                    name="recordings",
                    output_group_settings=aws.medialive.ChannelEncoderSettingsOutputGroupOutputGroupSettingsArgs(
                        archive_group_settings=[
                            aws.medialive.ChannelEncoderSettingsOutputGroupOutputGroupSettingsArchiveGroupSettingArgs(
                                destination=aws.medialive.ChannelEncoderSettingsOutputGroupOutputGroupSettingsArchiveGroupSettingDestinationArgs(
                                    destination_ref_id="recordings"
                                ),
                                rollover_interval=config.get_int("rollover_interval"),
                            )
                        ],
                    ),
                    outputs=[
                        aws.medialive.ChannelEncoderSettingsOutputGroupOutputArgs(
                            output_name="stream",
                            video_description_name="video",
                            audio_description_names=["audio"],
                            output_settings=aws.medialive.ChannelEncoderSettingsOutputGroupOutputOutputSettingsArgs(
                                archive_output_settings=aws.medialive.ChannelEncoderSettingsOutputGroupOutputOutputSettingsArchiveOutputSettingsArgs(
                                    container_settings=aws.medialive.ChannelEncoderSettingsOutputGroupOutputOutputSettingsArchiveOutputSettingsContainerSettingsArgs(
                                        m2ts_settings=aws.medialive.ChannelEncoderSettingsOutputGroupOutputOutputSettingsArchiveOutputSettingsContainerSettingsM2tsSettingsArgs()
                                    ),
                                    extension="ts",
                                    name_modifier="_$dt$",
                                )
                            ),
                        )
                    ],
                )
            ],
        ),
    )
    return _channel
