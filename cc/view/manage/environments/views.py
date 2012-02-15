# Case Conductor is a Test Case Management system.
# Copyright (C) 2011-2012 Mozilla
#
# This file is part of Case Conductor.
#
# Case Conductor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Case Conductor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Case Conductor.  If not, see <http://www.gnu.org/licenses/>.
"""
Manage views for environments.

"""
import json

from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

from cc import model

from cc.view.filters import ProfileFilterSet, EnvironmentFilterSet
from cc.view.lists import decorators as lists
from cc.view.utils.ajax import ajax

from ..finders import ManageFinder

from . import forms



@login_required
@lists.actions(
    model.Profile,
    ["delete", "clone"],
    permission="environments.manage_environments")
@lists.finder(ManageFinder)
@lists.filter("profiles", filterset_class=ProfileFilterSet)
@lists.sort("profiles")
@ajax("manage/environment/profile_list/_profiles_list.html")
def profiles_list(request):
    """List profiles."""
    return TemplateResponse(
        request,
        "manage/environment/profiles.html",
        {
            "profiles": model.Profile.objects.all(),
            }
        )



@login_required
def profile_details(request, profile_id):
    """Get details snippet for a profile."""
    profile = get_object_or_404(model.Profile, pk=profile_id)
    return TemplateResponse(
        request,
        "manage/environment/profile_list/_profile_details.html",
        {
            "profile": profile
            }
        )



@permission_required("environments.manage_environments")
def profile_add(request):
    """Add an environment profile."""
    if request.method == "POST":
        form = forms.AddProfileForm(request.POST, user=request.user)
        if form.is_valid():
            profile = form.save()
            messages.success(
                request, "Profile '{0}' added.".format(
                    profile.name)
                )
            return redirect("manage_profiles")
    else:
        form = forms.AddProfileForm(user=request.user)
    return TemplateResponse(
        request,
        "manage/environment/add_profile.html",
        {
            "form": form
            }
        )



@permission_required("environments.manage_environments")
@lists.filter("environments", filterset_class=EnvironmentFilterSet)
@lists.actions(
    model.Environment,
    ["delete"],
    permission="environments.manage_environments",
    fall_through=True)
@ajax("manage/environment/edit_profile/_envs_list.html")
def profile_edit(request, profile_id):
    profile = get_object_or_404(model.Profile, pk=profile_id)

    # @@@ should probably use a form
    if request.is_ajax() and request.method == "POST":
        if "save-profile-name" in request.POST:
            new_name = request.POST.get("profile-name")
            data = {}
            if not new_name:
                messages.error(request, "Please enter a profile name.")
                data["success"] = False
            else:
                profile.name = new_name
                profile.save(user=request.user)
                messages.success(request, "Profile name saved!")
                data["success"] = True

            return HttpResponse(
                json.dumps(data),
                content_type="application/json")

        elif "add-environment" in request.POST:
            element_ids = request.POST.getlist("element")
            if not element_ids:
                messages.error(
                    request, "Please select some environment elements.")
            else:
                env = model.Environment.objects.create(
                    profile=profile, user=request.user)
                env.elements.add(*element_ids)

    return TemplateResponse(
        request,
        "manage/environment/edit_profile.html",
        {
            "profile": profile,
            "environments": profile.environments.all(),
            }
        )


@login_required
def element_autocomplete(request):
    text = request.GET.get("text")
    elements = []
    if text is not None:
        elements = model.Environment.objects.filter(
            name__icontains=text)
    suggestions = []
    for e in elements:
        start = e.name.lower().index(text.lower())
        pre = e.name[:start]
        post = e.name[start+len(text):]
        suggestions.append({
                "preText": pre,
                "typedText": text,
                "postText": post,
                "id": e.id,
                "name": e.name,
                "type": "element",
                })
    return HttpResponse(
        json.dumps(
            {
                "suggestions": suggestions
                }
            ),
        content_type="application/json",
        )
