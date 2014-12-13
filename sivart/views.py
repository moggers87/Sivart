##
#    Copyright (C) 2014 Matt Molyneaux
#
#    This file is part of Sivart
#
#    Sivart is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Sivart is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Sivart.  If not, see <http://www.gnu.org/licenses/>.
##

from __future__ import unicode_literals

from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import Http404
from django.views import generic

from braces.views import SetHeadlineMixin
from travispy import TravisPy
from travispy.errors import TravisError

REDIRECT_PARAM = "repo"

class HomeView(SetHeadlineMixin, generic.TemplateView):
    template_name = "sivart/home.html"
    headline = "Home"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({"REDIRECT_PARAM": REDIRECT_PARAM})
        return context


class RepoView(SetHeadlineMixin, generic.TemplateView):
    template_name = "sivart/repo.html"

    def get_context_data(self, **kwargs):
        context = super(RepoView, self).get_context_data(**kwargs)
        context.update({"repo_slug": self.kwargs["repo_slug"], "repo": self.get_repo()})
        return context

    def get_headline(self):
        return "{0}".format(self.kwargs["repo_slug"])

    def get_repo(self):
        if not hasattr(self, "_repo"):
            try:
                self._repo = TravisPy().repo(self.kwargs["repo_slug"])
            except TravisError:
                self._repo = None

        if self._repo is None:
            raise Http404

        return self._repo


class RepoRedirectView(generic.RedirectView):
    permanent = False
    pattern_name = "repo"

    def get(self, *args, **kwargs):
        response = super(RepoRedirectView, self).get(*args, **kwargs)
        if response.status_code == 410:
            raise Http404
        else:
            return response

    def get_redirect_url(self, *args, **kwargs):
        kwargs.setdefault("repo_slug", self.request.GET.get(REDIRECT_PARAM))
        return super(RepoRedirectView, self).get_redirect_url(*args, **kwargs)
