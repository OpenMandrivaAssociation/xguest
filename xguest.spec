Summary: Creates xguest user as a locked down user 
Name: xguest
Version: 1.0.10
Release: 2
License: GPLv2+
Group:   System/Base
BuildArch: noarch
Source0:  http://people.fedoraproject.org/~dwalsh/xguest/%{name}-%{version}.tar.bz2
Source10: mkxguesthome
# (tv) prevent accessing other people accounts:
patch1: xguest-namespace2.patch
URL:     http://people.fedoraproject.org/~dwalsh/xguest/

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires(pre): pam >= 0.99.8.1 
Requires: dm
Conflicts: gdm < 2.20.10-6mdv
Conflicts: kdm < 2:4.3.1-12mdv
Conflicts: xdm < 1.1.8-4mdv

%if %mdkversion > 201000
%define grp_option -U
%else
%define grp_option %nil
%endif


# TODO:
# - check if /usr/sbin/gdm-safe-restart is needed in /etc/X11.gdm/PostSession/Default
# - prevent logging on console

%description
Installing this package sets up the xguest user to be used as a temporary
account to switch to or as a kiosk user account.
The user is only allowed to log in via gdm.  The home and temporary directories
of the user will be polyinstantiated and mounted on tmpfs.

WARNING: unlike Fedora, where the account is disabled unless SELinux is in
enforcing mode and where it's only accessible through gdm/kdm/xdm, it's
accessible from the console too.

%prep
%setup -q
%patch1 -p1 -b .home

%install
%{__rm} -fR %{buildroot}
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/desktop-profiles
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/security/namespace.d/ls
install -m0644 xguest.zip %{buildroot}/%{_sysconfdir}/desktop-profiles/
install -m0644 xguest.conf %{buildroot}/%{_sysconfdir}/security/namespace.d/

install -m0755 %SOURCE10 %{buildroot}%{_sysconfdir}/security/namespace.d/

# (tv) Using UID higher than UID_MAX=60000 from /etc/login.defs:
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/xguest-add-helper <<EOF
#!/bin/sh
groupdel xguest 2>/dev/null
userdel -r xguest 2>/dev/null

useradd -s /bin/rbash -K UID_MIN=61000 -K UID_MAX=65000 -K GID_MIN=61000 -K GID_MAX=65000 %grp_option -p '' -c "Guest Account" xguest || :

__eof

# prevent remote login:
if ! grep -q xguest /etc/ssh/denyusers; then
	echo xguest >> /etc/ssh/denyusers
fi

# prevent accessing most configuration tools (mcc still available with root password)
for i in /etc/pam.d/{mandriva-simple-auth,simple_root_authen,urpmi.update}; do
	fgrep -q xguest \$i && continue
	echo -e "\nauth\trequired\tpam_succeed_if.so\tquiet user != xguest" >> \$i
done
EOF

%post
if [ $1 -eq 1 ]; then
	xguest-add-helper
fi

%files
%defattr(-,root,root)
%attr(755,root,root) %_bindir/*
%config(noreplace) %{_sysconfdir}/desktop-profiles/xguest.zip
%{_sysconfdir}/security/namespace.d/
%doc README LICENSE

%preun
if [ $1 -eq 0 ]; then

userdel -r xguest
groupdel xguest

# remove forbiden SSH:
sed -i '/^xguest/d' /etc/ssh/denyusers

fi

%triggerun -- xguest <= 1.0.8-3mdv2010.0
userdel -r guest 2>/dev/null
xguest-add-helper


%changelog
* Sat May 07 2011 Oden Eriksson <oeriksson@mandriva.com> 1.0.8-7mdv2011.0
+ Revision: 671320
- mass rebuild

* Sat Dec 04 2010 Oden Eriksson <oeriksson@mandriva.com> 1.0.8-6mdv2011.0
+ Revision: 608210
- rebuild

* Tue Jan 12 2010 Thierry Vignaud <tv@mandriva.org> 1.0.8-5mdv2010.1
+ Revision: 490352
- relax "requires" for 2010.0
- set UID_MAX & GID_MAX too in order to prevent ID conflict
- no need to remove xguest on upgrade since helper already take care
- do not use useradd's -U option on 2010.0 (#56918)
- be safer and just delete xguest group before adding user else useradd
  may fail if group already exist

* Fri Jan 08 2010 Thierry Vignaud <tv@mandriva.org> 1.0.8-3mdv2010.1
+ Revision: 487450
- force creating a separate group and use high GID value (#54919)

* Thu Jan 07 2010 Thierry Vignaud <tv@mandriva.org> 1.0.8-2mdv2010.1
+ Revision: 487171
- use a restricted shell (suggested by G?\195?\182tz Waschk)
- prevent xguest user to access other user files (#54921)

* Thu Jan 07 2010 Thierry Vignaud <tv@mandriva.org> 1.0.8-1mdv2010.1
+ Revision: 487110
- new release
- adapt  to latest sabayon (#56357, Quel Qun)
- make sure to only add xguest once to /etc/ssh/denyusers (#56357)
- prevent accessing most configuration tools (mcc still available with
  root password) (#54900)
- ensure we get bumped xguest UID on update
- use UID higher than UID_MAX=60000 from /etc/login.defs so that new
  user accounts do not got high UIDs (#54919)

* Thu Oct 29 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-10mdv2010.0
+ Revision: 460111
- when upgrading from previous releases, remove guest account whithout deleting
  its contents (#54898)
- move %%post and %%pre scripts into xguest-add-helper script
- display user as "Guest Account" in DM instead of just "Guest"
- rename guest back to xguest (#54898)

* Mon Oct 19 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-9mdv2010.0
+ Revision: 458177
- use an even higher UID (10000 >) (#54479)

* Mon Oct 19 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-8mdv2010.0
+ Revision: 458174
- use an even higher UID (10000 >) (#54479)

* Wed Oct 14 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-7mdv2010.0
+ Revision: 457322
- use a high UID (1000 >) instead of a system UID (#54479)

* Mon Oct 12 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-6mdv2010.0
+ Revision: 456904
+ rebuild (emptylog)

* Mon Oct 12 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-5mdv2010.0
+ Revision: 456768
- use system UID (#54479)

* Tue Oct 06 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-4mdv2010.0
+ Revision: 454650
- only require new python-sabayon, not full sabayon
- require it for Requires(pre) too

* Mon Oct 05 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-3mdv2010.0
+ Revision: 454176
- rename xguest as guest

* Fri Oct 02 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-2mdv2010.0
+ Revision: 452592
- do not force a specific display manager, just conflicts with non aware ones

* Fri Oct 02 2009 Thierry Vignaud <tv@mandriva.org> 1.0.7-1mdv2010.0
+ Revision: 452553
- import xguest


* Wed Jul 22 2009 Thierry Vignaud <tvignaud@mandriva.com> 1.0.7-1mdv2010.0
- initial release
