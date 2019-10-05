from __future__ import unicode_literals

from moto.core.responses import BaseResponse
from moto.iam.models import ACCOUNT_ID
from moto.iam import iam_backend
from .exceptions import STSValidationError
from .models import sts_backend

MAX_FEDERATION_TOKEN_POLICY_LENGTH = 2048


class TokenResponse(BaseResponse):

    def get_session_token(self):
        duration = int(self.querystring.get('DurationSeconds', [43200])[0])
        token = sts_backend.get_session_token(duration=duration)
        template = self.response_template(GET_SESSION_TOKEN_RESPONSE)
        return template.render(token=token)

    def get_federation_token(self):
        duration = int(self.querystring.get('DurationSeconds', [43200])[0])
        policy = self.querystring.get('Policy', [None])[0]

        if policy is not None and len(policy) > MAX_FEDERATION_TOKEN_POLICY_LENGTH:
            raise STSValidationError(
                "1 validation error detected: Value "
                "'{\"Version\": \"2012-10-17\", \"Statement\": [...]}' "
                "at 'policy' failed to satisfy constraint: Member must have length less than or "
                " equal to %s" % MAX_FEDERATION_TOKEN_POLICY_LENGTH
            )

        name = self.querystring.get('Name')[0]
        token = sts_backend.get_federation_token(
            duration=duration, name=name, policy=policy)
        template = self.response_template(GET_FEDERATION_TOKEN_RESPONSE)
        return template.render(token=token, account_id=ACCOUNT_ID)

    def assume_role(self):
        role_session_name = self.querystring.get('RoleSessionName')[0]
        role_arn = self.querystring.get('RoleArn')[0]

        policy = self.querystring.get('Policy', [None])[0]
        duration = int(self.querystring.get('DurationSeconds', [3600])[0])
        external_id = self.querystring.get('ExternalId', [None])[0]

        role = sts_backend.assume_role(
            role_session_name=role_session_name,
            role_arn=role_arn,
            policy=policy,
            duration=duration,
            external_id=external_id,
        )
        template = self.response_template(ASSUME_ROLE_RESPONSE)
        return template.render(role=role)

    def assume_role_with_web_identity(self):
        role_session_name = self.querystring.get('RoleSessionName')[0]
        role_arn = self.querystring.get('RoleArn')[0]

        policy = self.querystring.get('Policy', [None])[0]
        duration = int(self.querystring.get('DurationSeconds', [3600])[0])
        external_id = self.querystring.get('ExternalId', [None])[0]

        role = sts_backend.assume_role_with_web_identity(
            role_session_name=role_session_name,
            role_arn=role_arn,
            policy=policy,
            duration=duration,
            external_id=external_id,
        )
        template = self.response_template(ASSUME_ROLE_WITH_WEB_IDENTITY_RESPONSE)
        return template.render(role=role)

    def get_caller_identity(self):
        template = self.response_template(GET_CALLER_IDENTITY_RESPONSE)

        # Default values in case the request does not use valid credentials generated by moto
        user_id = "AKIAIOSFODNN7EXAMPLE"
        arn = "arn:aws:sts::{account_id}:user/moto".format(account_id=ACCOUNT_ID)

        access_key_id = self.get_current_user()
        assumed_role = sts_backend.get_assumed_role_from_access_key(access_key_id)
        if assumed_role:
            user_id = assumed_role.user_id
            arn = assumed_role.arn

        user = iam_backend.get_user_from_access_key_id(access_key_id)
        if user:
            user_id = user.id
            arn = user.arn

        return template.render(account_id=ACCOUNT_ID, user_id=user_id, arn=arn)


GET_SESSION_TOKEN_RESPONSE = """<GetSessionTokenResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <GetSessionTokenResult>
    <Credentials>
      <SessionToken>AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE/IvU1dYUg2RVAJBanLiHb4IgRmpRV3zrkuWJOgQs8IZZaIv2BXIa2R4OlgkBN9bkUDNCJiBeb/AXlzBBko7b15fjrBs2+cTQtpZ3CYWFXG8C5zqx37wnOE49mRl/+OtkIKGO7fAE</SessionToken>
      <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY</SecretAccessKey>
      <Expiration>{{ token.expiration_ISO8601 }}</Expiration>
      <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
    </Credentials>
  </GetSessionTokenResult>
  <ResponseMetadata>
    <RequestId>58c5dbae-abef-11e0-8cfe-09039844ac7d</RequestId>
  </ResponseMetadata>
</GetSessionTokenResponse>"""


GET_FEDERATION_TOKEN_RESPONSE = """<GetFederationTokenResponse xmlns="https://sts.amazonaws.com/doc/
2011-06-15/">
  <GetFederationTokenResult>
    <Credentials>
      <SessionToken>AQoDYXdzEPT//////////wEXAMPLEtc764bNrC9SAPBSM22wDOk4x4HIZ8j4FZTwdQWLWsKWHGBuFqwAeMicRXmxfpSPfIeoIYRqTflfKD8YUuwthAx7mSEI/qkPpKPi/kMcGdQrmGdeehM4IC1NtBmUpp2wUE8phUZampKsburEDy0KPkyQDYwT7WZ0wq5VSXDvp75YU9HFvlRd8Tx6q6fE8YQcHNVXAkiY9q6d+xo0rKwT38xVqr7ZD0u0iPPkUL64lIZbqBAz+scqKmlzm8FDrypNC9Yjc8fPOLn9FX9KSYvKTr4rvx3iSIlTJabIQwj2ICCR/oLxBA==</SessionToken>
      <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY</SecretAccessKey>
      <Expiration>{{ token.expiration_ISO8601 }}</Expiration>
      <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
    </Credentials>
    <FederatedUser>
      <Arn>arn:aws:sts::{{ account_id }}:federated-user/{{ token.name }}</Arn>
      <FederatedUserId>{{ account_id }}:{{ token.name }}</FederatedUserId>
    </FederatedUser>
    <PackedPolicySize>6</PackedPolicySize>
  </GetFederationTokenResult>
  <ResponseMetadata>
    <RequestId>c6104cbe-af31-11e0-8154-cbc7ccf896c7</RequestId>
  </ResponseMetadata>
</GetFederationTokenResponse>"""


ASSUME_ROLE_RESPONSE = """<AssumeRoleResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <AssumeRoleResult>
    <Credentials>
      <SessionToken>{{ role.session_token }}</SessionToken>
      <SecretAccessKey>{{ role.secret_access_key }}</SecretAccessKey>
      <Expiration>{{ role.expiration_ISO8601 }}</Expiration>
      <AccessKeyId>{{ role.access_key_id }}</AccessKeyId>
    </Credentials>
    <AssumedRoleUser>
      <Arn>{{ role.arn }}</Arn>
      <AssumedRoleId>{{ role.user_id }}</AssumedRoleId>
    </AssumedRoleUser>
    <PackedPolicySize>6</PackedPolicySize>
  </AssumeRoleResult>
  <ResponseMetadata>
    <RequestId>c6104cbe-af31-11e0-8154-cbc7ccf896c7</RequestId>
  </ResponseMetadata>
</AssumeRoleResponse>"""


ASSUME_ROLE_WITH_WEB_IDENTITY_RESPONSE = """<AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <AssumeRoleWithWebIdentityResult>
    <Credentials>
      <SessionToken>{{ role.session_token }}</SessionToken>
      <SecretAccessKey>{{ role.secret_access_key }}</SecretAccessKey>
      <Expiration>{{ role.expiration_ISO8601 }}</Expiration>
      <AccessKeyId>{{ role.access_key_id }}</AccessKeyId>
    </Credentials>
    <AssumedRoleUser>
      <Arn>{{ role.arn }}</Arn>
      <AssumedRoleId>ARO123EXAMPLE123:{{ role.session_name }}</AssumedRoleId>
    </AssumedRoleUser>
    <PackedPolicySize>6</PackedPolicySize>
  </AssumeRoleWithWebIdentityResult>
  <ResponseMetadata>
    <RequestId>c6104cbe-af31-11e0-8154-cbc7ccf896c7</RequestId>
  </ResponseMetadata>
</AssumeRoleWithWebIdentityResponse>"""


GET_CALLER_IDENTITY_RESPONSE = """<GetCallerIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <GetCallerIdentityResult>
    <Arn>{{ arn }}</Arn>
    <UserId>{{ user_id }}</UserId>
    <Account>{{ account_id }}</Account>
  </GetCallerIdentityResult>
  <ResponseMetadata>
    <RequestId>c6104cbe-af31-11e0-8154-cbc7ccf896c7</RequestId>
  </ResponseMetadata>
</GetCallerIdentityResponse>
"""
