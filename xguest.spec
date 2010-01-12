Summary: Creates xguest user as a locked down user 
Name: xguest
Version: 1.0.8
Release: %mkrel 3
License: GPLv2+
Group:   System/Base
BuildArch: noarch
Source:  http://people.fedoraproject.org/~dwalsh/xguest/%{name}-%{version}.tar.bz2
Source10: mkxguesthome
patch:   xguest-namespace.patch
# (tv) prevent accessing other people accounts:
patch1: xguest-namespace2.patch
URL:     http://people.fedoraproject.org/~dwalsh/xguest/

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires(pre): pam >= 0.99.8.1 python-sabayon
Requires(post): python-sabayon
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
%patch -p1 -b .namespace
%patch1 -p1 -b .home

%build

%clean
%{__rm} -fR %{buildroot}

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
groupdel xguest 2>/dev/null
userdel -r xguest 2>/dev/null

useradd -s /bin/rbash -K UID_MIN=61000 -K GID_MIN=61000 %grp_option -p '' -c "Guest Account" xguest || :

# Add two directories to /etc/skell so pam_namespace will label properly
mkdir /etc/skel/.mozilla 2> /dev/null
mkdir /etc/skel/.gnome2 2> /dev/null

/usr/bin/python << __eof
%if %mdkversion > 201000
from sabayon import systemdb
db = systemdb.get_user_database()
%else
from sabayon import userdb
db = userdb.get_database()
%endif

db.set_profile("xguest", "xguest.zip")
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

/usr/bin/python << __eof
%if %mdkversion > 201000
from sabayon import systemdb
db = systemdb.get_user_database()
%else
from sabayon import userdb
db = userdb.get_database()
%endif
db.set_profile("xguest", "")
__eof

userdel -r xguest
groupdel xguest

# remove forbiden SSH:
sed -i '/^xguest/d' /etc/ssh/denyusers

fi

%triggerun -- xguest <= 1.0.8-2mdv2010.1
userdel -r guest 2>/dev/null
xguest-add-helper
