from typing import Union, Optional, Callable

from django.http import HttpResponseBadRequest, HttpResponse

from its_utils.app_get_params.decorators import expect_param, CoerceFn, CoercePair, missing, ParamType


class AdminModeViewParam:
    DECORATOR = staticmethod(expect_param)

    def __init__(self,
                 from_: str = 'its_params',
                 coerce: Union[CoerceFn, CoercePair, None] = None,
                 default: Optional[ParamType] = missing,
                 as_: Optional[str] = None,
                 err: Callable[[str], HttpResponse] = HttpResponseBadRequest):
        """
        Параметры для expect_param
        """

        self.from_ = from_
        self.coerce = coerce
        self.default = default
        self.as_ = as_
        self.err = err

    def decorate(self, view: Callable, param_name: str) -> Callable:
        """
        Применить expect_param к view
        """

        return self.DECORATOR(
            param=param_name,
            from_=self.from_,
            coerce=self.coerce,
            default=self.default,
            as_=self.as_,
            err=self.err,
        )(view)
